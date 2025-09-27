#!/bin/bash

# Set sane bash defaults
set -o errexit
set -o pipefail

JMAP_USERNAME=${JMAP_USERNAME}
JMAP_TOKEN=${JMAP_TOKEN}
JMAP_HOSTNAME=${JMAP_HOSTNAME}
JMAP_MAILBOXES=${JMAP_MAILBOXES} # Semi-colon separated list of mailboxes to back up
CRON_SCHEDULE=${CRON_SCHEDULE:-0 * * * *}
CLI_PARAMS=${CLI_PARAMS:-""}

LOCKFILE="/tmp/jmap-backup.lock"
LOG="/var/log/cron.log"


if [ ! -e $LOG ]; then
  touch $LOG
fi

CRONFILE="/etc/cron.d/jmap-backup"
CRONENV=""


echo "Adding CRON schedule: $CRON_SCHEDULE"
echo "PATH=\"$PATH\"" > $CRONFILE
echo "SHELL=/bin/bash" >> $CRONFILE
CRONENV="$CRONENV JMAP_USERNAME=$JMAP_USERNAME"
CRONENV="$CRONENV JMAP_TOKEN=$JMAP_TOKEN"
CRONENV="$CRONENV JMAP_HOSTNAME=$JMAP_HOSTNAME"
CRONENV="$CRONENV JMAP_MAILBOXES=\"$JMAP_MAILBOXES\""
CRONENV="$CRONENV CLI_PARAMS=\"$CLI_PARAMS\""
echo "$CRON_SCHEDULE root cd /app && $CRONENV ./backup.sh >> /var/log/cron.log 2>&1" >> $CRONFILE
#echo "$CRON_SCHEDULE root $CRONENV echo hi" > $CRONFILE

echo "Starting CRON scheduler: $(date)"
cron
exec tail -f $LOG 2> /dev/null