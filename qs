#!/usr/bin/env bash

set -e
category=$1
# Possible categories
container_commands=("run" "stop" "restart" "logs" "exec")

## Container Commands ##
if [[ " ${container_commands[*]} " =~ " ${category} " ]]; then
    compose_args=("--env-file")
    post_args=()
    dev_type=$2
    # options: prod, dev

    # set the env files needed
    case $dev_type in
        dev)
            env_file="config/.env.dev"
            compose_args+=($env_file)
            ;;
        prod)
            env_file="config/.env.prod"
            compose_args+=($env_file "--file" "compose.prod.yaml")
            ;;
    esac
    # configure the container command
    case $category in
        run)
            compose_args+=("up" "-d")
            ;;&
        restart)
            compose_args+=("restart")
            ;;&
        run | restart)
            . $env_file && post_args+=("echo" "Application available at http://localhost:${ACCESS_PORT}")
            ;;
        stop)
            compose_args+=("down")
            ;;
        logs)
            compose_args+=("logs")
            ;;
        exec)
            compose_args+=("exec" "web" "bash")
            ;;
    esac
    extra_args=${@:3}
    docker compose ${compose_args[@]} ${extra_args[@]}
    "${post_args[@]}"
fi

## Backup Commands ##
if [ $category == "backup" ]; then
    action=$2
    con_type=${3:-prod}
    config_file="config/.env.${con_type}"
    . $config_file
    case $action in
    install|update)
        mkdir -p $SNCRS_BACKUP_DIR
        cp $config_file $SNCRS_BACKUP_DIR/
        script_location=$SNCRS_BACKUP_DIR/backup.sh 
        cp "backup/backup.sh" $script_location
        ;;&
    install)
        if crontab -l | grep -q "$script_location $con_type" ; then
            echo "Cron job already installed"
        else
            (crontab -l 2>/dev/null; echo "0 12 * * * $script_location $con_type") | crontab -
        fi
        ;;
    now)
        local_file="$4"
        script_location="$SNCRS_BACKUP_DIR/backup.sh"
        if [ -f $script_location ]; then
            $script_location $con_type $local_file
        else
            echo "Backup script is not correctly placed, please run 'qs backup install'"
        fi
        ;;
    restore)
        backup_file_location="$4"
        if ! [ -e $backup_file_location ]; then
            echo "Error: There is no file available at $backup_file_location"
            exit 1
        fi
        sncrs_postgres_container=$(docker container ls | grep "sncrs_$con_type"'[^ ]*db' | head -n 1 | cut -f1,1 -d" ")
        if [ -z $sncrs_postgres_container ]; then
            echo "Error: The sncrs postgres container is not available, can't restore backup"
            exit 1
        fi
        sncrs_web_container=$(docker container ls | grep "sncrs_$con_type"'[^ ]*web' | head -n 1 | cut -f1,1 -d" ")
        if [ -z $sncrs_web_container ]; then
            echo "Error: The sncrs web container is not available, can't restore backup"
            exit 1
        fi
        WORK_DIR=$(mktemp -d)
        trap "rm -rf $WORK_DIR" EXIT
        cp $backup_file_location $WORK_DIR/restore.tar.gz
        tar xzf $WORK_DIR/restore.tar.gz -C $WORK_DIR
        # Extra slashes in the two lines below are to prevent
        # Git Bash from expanding to windows paths
        docker cp $WORK_DIR/backup/media/. $sncrs_web_container://sncrs/media
        docker exec $sncrs_web_container chown -R www-data:www-data //sncrs/media
        cat $WORK_DIR/backup/sncrs-db.sql | docker exec -i $sncrs_postgres_container psql -U $POSTGRES_USER -d postgres
        ;;
    esac
fi
