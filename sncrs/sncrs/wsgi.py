"""
WSGI config for sncrs project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

sys.path.append(os.environ.get("SNCRS_PRODUCTION_REPO_PATH"))
sys.path.append(os.environ.get("SNCRS_PRODUCTION_VENV_SITE_PACKAGES_PATH"))

os.environ['DJANGO_SETTINGS_MODULE'] = 'sncrs.settings'

application = get_wsgi_application()
