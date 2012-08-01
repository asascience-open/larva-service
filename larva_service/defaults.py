import os

DEBUG = False
TESTING = False
LOG_FILE = False

SECRET_KEY = os.environ.get("SECRET_KEY")

# Celery
CELERY_IMPORTS = ("larva_service.tasks", )
