import click
import os

from slugify import slugify
import structlog

from jmap_backup.tiny_jmap import TinyJMAPClient
from jmap_backup.utils import read_state, write_state, build_message, download_blob, write_eml_file

DATA_DIR = os.environ["DATA_DIR"]
APPDATA_DIR = os.environ["APPDATA_DIR"]
logger = structlog.get_logger()

@click.group()
@click.version_option()
def cli():
    "A CLI tool to backup a mailbox using the JMAP protocol"


@cli.command(name="top-n")
@click.option(
    "-n",
    default=10,
    help="Number of messages to show (default: 10)",
)
def top_n(n):
    "Command description goes here"
    client = TinyJMAPClient(
        hostname=os.environ.get("JMAP_HOSTNAME", "api.fastmail.com"),
        username=os.environ.get("JMAP_USERNAME"),
        token=os.environ.get("JMAP_TOKEN"),
    )

@cli.command(name="sync-mailbox")
@click.option(
    "-m",
    "--mailbox",
    required=True,
    help="Name of the mailbox to sync",
)
@click.option(
    "-s",
    "--state-file",
    default=f"{APPDATA_DIR}/jmap_state.json",
    help="Path to the state file (default: APPDATA_DIR/jmap_state.json)",
)
def sync_mailbox(mailbox, state_file):
    "Sync a mailbox"
    client = TinyJMAPClient(
        hostname=os.environ.get("JMAP_HOSTNAME", "api.fastmail.com"),
        username=os.environ.get("JMAP_USERNAME"),
        token=os.environ.get("JMAP_TOKEN"),
    )
    account_id = client.get_account_id()
    mailbox_list = client.make_jmap_call(
        {
            "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
            "methodCalls": [
                [
                    "Mailbox/query",
                    {
                        "accountId": account_id,
                        "filter": {"name": mailbox},
                    },
                    "0",
                ]
            ],
        }
    )
    if len(mailbox_list['methodResponses'][0][1]['ids']) == 0:
        logger.warning(f"Mailbox not found", mailbox=mailbox)
        return
    mailbox_id = mailbox_list['methodResponses'][0][1]['ids'][0]
    logger.debug(f"Mailbox ID", mailbox_id=mailbox_id, mailbox=mailbox)
    
    state = read_state(state_file)

    if mailbox not in state:
        state[mailbox] = {"state": "null", "position": 0}

    if state[mailbox]["state"] == "null":
        logger.info("No previous state found, performing full sync", mailbox=mailbox)

        logger.info(f"Starting at position {state[mailbox]["position"]}", mailbox=mailbox, position=state[mailbox]["position"])
        
        more_items = True
        while more_items:
            email_res = client.make_jmap_call(
                {
                    "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
                    "methodCalls": [
                        [ 
                            "Email/query", {
                                "accountId": account_id,
                                "filter": {
                                    "inMailbox": mailbox_id
                                },
                                "sort": [{
                                    "property": "receivedAt",
                                    "isAscending": True
                                }],
                                "position": state[mailbox]["position"],
                                "collapseThreads": False,
                                "limit": 100,
                                "calculateTotal": True
                            }, 
                            "0" 
                        ],
                        [ 
                            "Email/get", {
                                "accountId": account_id,
                                "#ids": {
                                    "name": "Email/query",
                                    "path": "/ids",
                                    "resultOf": "0"
                                },
                                "properties": [ "bodyStructure", "bodyValues", "threadId", "subject", "from", "receivedAt"],
                                "bodyProperties": [ "partId", "blobId", "name", "headers", "type"],
                                "fetchAllBodyValues": True,
                            }, 
                            "1" 
                        ]
                    ]
                }
            )
            logger.info(f"Fetched {len(email_res['methodResponses'][1][1]['list'])} emails", mailbox=mailbox)
            if len(email_res['methodResponses'][1][1]['list']) == 0:
                logger.info("No more emails to fetch")
                more_items = False
                state[mailbox]["state"] = email_res['methodResponses'][0][1]['queryState']
                write_state(state_file, state)
                break
            for email in email_res['methodResponses'][1][1]['list']:
                logger.info(f"Processing email", from_email=email['from'], subject=email['subject'])
                try:
                    msg = build_message(email, client)
                    write_eml_file(msg, f"{DATA_DIR}/{mailbox}/{slugify(email["from"][0]["email"])}/{slugify(email["threadId"])}/{slugify(email["receivedAt"])}-{slugify(email["subject"])}-{slugify(email["id"])}.eml")
                except Exception as e:
                    logger.exception(f"Failed to process email", from_email=email['from'], subject=email['subject'], id=email['id'])
                    state[mailbox]["errors"] = state[mailbox].get("errors", []) + [email['id']]
                else:
                    state[mailbox]["position"] += 1
                write_state(state_file, state)
    else:
        logger.info("Previous state found, performing incremental sync")
        email_res = client.make_jmap_call(
            {
                "using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
                "methodCalls": [
                    [ 
                        "Email/queryChanges", {
                            "accountId": account_id,
                            "filter": {
                                "inMailbox": mailbox_id
                            },
                            "sort": [{
                                "property": "receivedAt",
                                "isAscending": True
                            }],
                            "sinceQueryState": state[mailbox]["state"],
                            "collapseThreads": False,
                            "calculateTotal": True
                        }, 
                        "0" 
                    ],
                    [ 
                        "Email/get", {
                            "accountId": account_id,
                            "#ids": {
                                "name": "Email/queryChanges",
                                "path": "/added/*/id",
                                "resultOf": "0"
                            },
                            "properties": [ "bodyStructure", "bodyValues", "threadId", "subject", "from", "receivedAt"],
                            "bodyProperties": [ "partId", "blobId", "name", "headers", "type"],
                            "fetchAllBodyValues": True,
                        }, 
                        "1" 
                    ]
                ]
            }
        )
        logger.info(f"Fetched {len(email_res['methodResponses'][1][1]['list'])} emails", mailbox=mailbox)
        for email in email_res['methodResponses'][1][1]['list']:
            logger.info(f"Processing email", from_email=email['from'], subject=email['subject'])
            try:
                msg = build_message(email, client)
                write_eml_file(msg, f"{DATA_DIR}/{mailbox}/{slugify(email["from"][0]["email"])}/{slugify(email["threadId"])}/{slugify(email["receivedAt"])}-{slugify(email["subject"])}-{slugify(email["id"])}.eml")
            except Exception as e:
                logger.exception(f"Failed to process email", from_email=email['from'], subject=email['subject'], id=email['id'])
                state[mailbox]["errors"] = state[mailbox].get("errors", []) + [email['id']]
        state[mailbox]["state"] = email_res['methodResponses'][0][1]['newQueryState']
        write_state(state_file, state)
