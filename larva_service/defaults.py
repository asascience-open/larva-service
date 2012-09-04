import os

DEBUG = False
TESTING = False
LOG_FILE = False

SECRET_KEY = os.environ.get("SECRET_KEY")

# Celery
BROKER_URL = os.environ.get('BROKER_URL')
CELERY_IMPORTS = ("larva_service.tasks", )
