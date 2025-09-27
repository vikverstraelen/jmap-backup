from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email import generator

from urllib.request import Request, urlopen
from urllib.parse import quote_plus
from slugify import slugify
from base64 import b64encode
from pathlib import Path

from textwrap import wrap
import re
import json

from jmap_backup.tiny_jmap import TinyJMAPClient

def download_blob(blob_id, name, full_type, client):
    account_id = client.get_account_id()
    download_url = client.session["downloadUrl"] \
        .replace("{accountId}", account_id)      \
        .replace("{blobId}", blob_id)            \
        .replace("{name}", slugify(name))                 \
        .replace("{type}", full_type)
    print(f"Downloading attachment from {download_url}")
    r = Request(
        download_url, 
        headers={
            "Authorization": f"Bearer {client.token}",
        },)
    f = urlopen(r)
    data = f.read()
    return "\n".join(wrap(str(b64encode(data), 'utf-8'), 76))


def build_message(jmap_email_response, client):
    body_structure = jmap_email_response['bodyStructure']
    return build_message_part(body_structure, jmap_email_response, client)

def build_message_part(sub_part, jmap_email_res, client):
    full_type = sub_part['type']
    main_type = full_type.split('/')[0]
    subtype = full_type.split('/')[1]
    headers = {h['name']: h['value'] for h in sub_part.get('headers', [])}
    if main_type == 'multipart':
        msg_part = MIMEMultipart(subtype if subtype else 'mixed')
        for part in sub_part['subParts']:
            msg_part.attach(build_message_part(part, jmap_email_res, client))
    elif main_type == 'text':
        part_id = sub_part['partId']
        charset = None
        if 'Content-Type' in headers:
            # Try to extract charset from Content-Type header
            match = re.search(r'charset=([^\s;]+)', headers['Content-Type'], re.IGNORECASE)
            if match:
                charset = match.group(1).strip('"').strip("'")
        msg_part = MIMEText(
            jmap_email_res['bodyValues'][part_id]['value'], _subtype=subtype, _charset=charset)
    else:
        part_id = sub_part['partId']
        blob_id = sub_part['blobId']
        name = sub_part['name'] or 'attachment'
        msg_part = MIMENonMultipart(main_type, subtype)
        msg_part.set_payload(download_blob(blob_id, name, full_type, client))
    
    for header in sub_part.get('headers', []):
        if header['name'] == 'Content-Type':
            continue
        if header['name'] == 'Content-Transfer-Encoding' and main_type == 'text':
            continue
        msg_part.add_header(header['name'], header['value'].replace('\r', '').replace('\n', ''))
    return msg_part


def read_state(state_file):
    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {}
    return state

def write_state(state_file, state):
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def write_eml_file(msg, filename):
    output_file = Path(filename)
    output_file.parent.mkdir(exist_ok=True, parents=True)
    with open(filename, 'w') as file:
        emlGenerator = generator.Generator(file)
        emlGenerator.flatten(msg)
