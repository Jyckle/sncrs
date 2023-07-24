#!/usr/bin/env bash

set -e
category=$1
# Possible categories
container_commands=("run" "stop" "restart" "logs")

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
        down)
            compose_args+=("down")
            ;;
        logs)
            compose_args+=("logs")
            ;;
    esac
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
