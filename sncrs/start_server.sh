#!/usr/bin/env bash
# start-server.sh
echo 'Waiting for postgres...'

while ! nc -z $DB_HOSTNAME $DB_PORT; do
    sleep 0.1
done

echo 'PostgreSQL started'

(cd /sncrs/; python manage.py collectstatic --no-input; python manage.py makemigrations --no-input; python manage.py migrate --no-input)

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] ; then
    (cd /sncrs/; python manage.py createsuperuser --no-input)
fi

reload_args=()
if [ "$LIVE_RELOAD" = "true" ]; then
    reload_args=('--reload')
fi

(cd /sncrs/; gunicorn sncrs.wsgi ${reload_args[@]} --timeout 1200 --user www-data --bind 0.0.0.0:8010 --workers 3) &
nginx -g "daemon off;"