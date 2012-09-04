import os

from flask import Flask
from flask.ext.mongokit import MongoKit

from celery import Celery

# Create application object
app = Flask(__name__)

app.config.from_object('larva_service.defaults')
app.config.from_envvar('APPLICATION_SETTINGS', silent=True)

class CeleryConfig(object):
    CELERY_DEFAULT_QUEUE = 'default'
    CELERY_RESULT_BACKEND = 'mongodb'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_TRACK_STARTED = True
    CELERY_REDIS_MAX_CONNECTIONS = app.config.get('CELERY_REDIS_MAX_CONNECTIONS', 10)
    CELERY_ROUTES = { 'larva_service.tasks.dataset.calc': {'queue': 'datasets'},
                      'larva_service.tasks.larva.run':  {'queue': 'runs'}}
    CELERY_MONGODB_BACKEND_SETTINGS = {
        "host"                  : app.config.get("MONGODB_HOST"),
        "port"                  : app.config.get("MONGODB_PORT"),
        "user"                  : app.config.get("MONGODB_USERNAME"),
        "password"              : app.config.get("MONGODB_PASSWORD"),
        "database"              : app.config.get("MONGODB_DATABASE"),
        "taskmeta_collection"   : 'tasks'
    }
app.config.from_object(CeleryConfig)

# Create logging
if app.config.get('LOG_FILE') == True:
    import logging
    from logging import FileHandler
    file_handler = FileHandler('log.txt')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

# Create celery object
celery = Celery(__name__)
# Now configure celety
celery.conf.add_defaults(app.config)

# Create the database connection
db = MongoKit(app)

# Import everything
import larva_service.views
import larva_service.models
import larva_service.tasks