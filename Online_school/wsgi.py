"""
WSGI config for Online_school project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

# Monkey patch для gevent должен быть первым
if os.environ.get('GEVENT_SUPPORT') == 'True':
    from gevent import monkey
    monkey.patch_all()
    
    # Патч для psycopg2 + gevent
    import psycogreen.gevent
    psycogreen.gevent.patch_psycopg()

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Online_school.settings')

application = get_wsgi_application()
