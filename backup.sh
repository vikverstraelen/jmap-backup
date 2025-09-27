#!/bin/bash

# Set sane bash defaults
set -o errexit
set -o pipefail

JMAP_USERNAME=${JMAP_USERNAME}
JMAP_TOKEN=${JMAP_TOKEN}
JMAP_HOSTNAME=${JMAP_HOSTNAME}
JMAP_MAILBOXES=${JMAP_MAILBOXES} # Semi-colon separated list of mailboxes to back up
CLI_PARAMS=${CLI_PARAMS:-""}
export DATA_DIR=${DATA_DIR:-"/data"}

IFS=$';'
source .venv/bin/activate
for mailbox in $JMAP_MAILBOXES
do
    echo "Syncing mailbox: $mailbox to $DATA_DIR"
    jmap-backup sync-mailbox -m "$mailbox" $CLI_PARAMS
done