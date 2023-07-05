#!/bin/bash

set -ex
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

WORK_DIR=$(mktemp -d)
trap "rm -rf $WORK_DIR" EXIT

. $SCRIPT_DIR/.env
sncrs_postgres_container=$(docker container ls | grep 'sncrs_prod[^ ]*db' | head -n 1 | cut -f1,1 -d" ")
if [ -z $sncrs_postgres_container ]; then
    echo "Error: The sncrs postgres container is not available, can't backup"
    exit 1
fi
BACKUP_FILE_PATH=${WORK_DIR}/sncrs-$(date '+%Y%m%d-%H%M').gz
docker exec ${sncrs_postgres_container} pg_dump -c -U ${POSTGRES_USER} -d ${POSTGRES_DB} | gzip > $BACKUP_FILE_PATH
for dest in "$RCLONE_DESTS"; do
    rclone -vv --no-check-dest copy "${BACKUP_FILE_PATH}" "${dest}"
done
