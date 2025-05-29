"""
WSGI config for Online_school project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
import logging

# Настраиваем базовое логирование для диагностики
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

try:
    logger.info("WSGI: Starting initialization...")
    
    # Проверяем переменные окружения
    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'Online_school.settings')
    logger.info(f"WSGI: Using settings module: {settings_module}")
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    
    logger.info("WSGI: Importing Django WSGI application...")
    from django.core.wsgi import get_wsgi_application
    
    logger.info("WSGI: Getting WSGI application...")
    application = get_wsgi_application()
    
    logger.info("WSGI: Successfully initialized Django application")
    
except Exception as e:
    logger.error(f"WSGI: Failed to initialize Django application: {e}")
    logger.exception("WSGI: Full traceback:")
    raise
