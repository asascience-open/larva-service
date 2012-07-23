import os

from flask import Flask
from flask.ext.mongokit import MongoKit

from celery import Celery

# Create application object
app = Flask(__name__)
app.config.from_object('larva_service.defaults')
app.config.from_envvar('APPLICATION_SETTINGS', silent=True)

# Celery config
class CeleryConfig:
    CELERY_RESULT_BACKEND = "mongodb"
    CELERY_MONGODB_BACKEND_SETTINGS = {
        "host": app.config['MONGODB_HOST'],
        "port": app.config['MONGODB_PORT'],
        "user": app.config['MONGODB_USERNAME'],
        "pass": app.config['MONGODB_PASSWORD'],
        "database": app.config['MONGODB_DATABASE'],
        "taskmeta_collection": "tasks"
    }
app.config.from_object(CeleryConfig)

# Create celery object
celery = Celery(__name__)
# Now configure celety
celery.config_from_object(app.config)

# Create logging
if app.config.get('LOG_FILE') == True:
    import logging
    from logging import FileHandler
    file_handler = FileHandler('log.txt')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

# Create the database connection
db = MongoKit(app)

# Import everything
import larva_service.views
import larva_service.models
import larva_service.tasks