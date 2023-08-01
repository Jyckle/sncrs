#!/bin/bash

set -ex
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
con_type=${1:-prod}
local_file_dest=$2

WORK_DIR=$(mktemp -d)
trap "rm -rf $WORK_DIR" EXIT

. $SCRIPT_DIR/.env.${con_type}
sncrs_postgres_container=$(docker container ls | grep 'sncrs_'"$con_type"'[^ ]*db' | head -n 1 | cut -f1,1 -d" ")
if [ -z $sncrs_postgres_container ]; then
    echo "Error: The sncrs postgres container is not available, can't backup"
    exit 1
fi
BACKUP_FILE_NAME="sncrs-$con_type-$(date '+%Y%m%d-%H%M').tar.gz"
BACKUP_FILE_PATH=${WORK_DIR}/${BACKUP_FILE_NAME}
DB_BACKUP_PATH=${WORK_DIR}/sncrs-db.sql
docker exec ${sncrs_postgres_container} pg_dumpall -c -U ${POSTGRES_USER} > $DB_BACKUP_PATH
sncrs_web_container=$(docker container ls | grep 'sncrs_'"$con_type"'[^ ]*web' | head -n 1 | cut -f1,1 -d" ")
if [ -z $sncrs_web_container ]; then
    echo "Error: The sncrs web container is not available, can't backup"
    exit 1
fi
# Copy the media files into the backup location
docker run -v ${WORK_DIR}:/backup --rm --volumes-from $sncrs_web_container ubuntu bash -c "cp -r /sncrs/media /backup/media && chmod -R 777 /backup && tar czf /tmp/${BACKUP_FILE_NAME} /backup && cp /tmp/${BACKUP_FILE_NAME} /backup/"
if [ -n "$local_file_dest" ]; then
    cp "${BACKUP_FILE_PATH}" "${local_file_dest}"
else
    for dest in "$RCLONE_DESTS"; do
        rclone -vv --no-check-dest copy "${BACKUP_FILE_PATH}" "${dest}"
    done
fi