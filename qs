#!/usr/bin/env bash

set -e
category=$1
# Possible categories
# run, stop, backup

## Container Commands ##
if [ $category == "run" ] || [ $category == "stop" ] || [ $category == "restart" ]; then
    compose_args=("--env-file")
    post_args=()
    dev_type=$2
    # options: prod, dev

    # set the env files needed
    if [ $dev_type == "dev" ]; then
        env_file="config/.env.dev"
        compose_args+=($env_file)
    elif [ $dev_type == "prod" ]; then
        env_file="config/.env.prod"
        compose_args+=($env_file "--file" "compose.prod.yaml")
    fi
    # configure the container command
    if [ $category == "run" ]; then
        compose_args+=("up" "-d")
        . $env_file && post_args+=("echo" "Application available at http://localhost:${ACCESS_PORT}")
    elif [ $category == "stop" ]; then
        compose_args+=("down")
    elif [ $category == "restart" ]; then
        compose_args+=("restart")
        . $env_file && post_args+=("echo" "Application available at http://localhost:${ACCESS_PORT}")
    fi
    extra_args=${@:3}
    docker compose ${compose_args[@]} ${extra_args[@]}
    "${post_args[@]}"
fi

## Backup Commands ##
if [ $category == "backup" ]; then
    action=$2
    . "config/.env.prod"
    if [ $action == "install" ]; then
        mkdir -p $SNCRS_BACKUP_DIR
        cp "config/.env.prod" $SNCRS_BACKUP_DIR/.env
        script_location=$SNCRS_BACKUP_DIR/backup.sh 
        cp "backup/backup.sh" $script_location
        if crontab -l | grep -q $script_location ; then
            echo "Cron job already installed"
        else
            (crontab -l 2>/dev/null; echo "0 12 * * * $script_location") | crontab -
        fi
    elif [ $action == "now" ]; then
        script_location="$SNCRS_BACKUP_DIR/backup.sh"
        if [ -f $script_location ]; then
            $script_location
        else
            echo "Backup script is not correctly placed, please run 'qs backup install'"
        fi
    fi
fi
