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
    CELERY_RESULT_BACKEND = app.config.get("BROKER_URL")
    #CELERY_TASK_SERIALIZER = 'json'
    CELERY_TRACK_STARTED = True
    CELERY_ROUTES = { 'larva_service.tasks.dataset.calc': {'queue': 'datasets'},
                      'larva_service.tasks.larva.run':  {'queue': 'runs'}}
app.config.from_object(CeleryConfig)

# Setup CACHE_PATH
if app.config.get('CACHE_PATH', None) is None:
    app.config['CACHE_PATH'] = os.path.join(os.path.dirname(__file__), "..","cache")
if not os.path.exists(app.config['CACHE_PATH']):
    os.makedirs(app.config['CACHE_PATH'])

# Setup OUTPUT_PATH
if app.config.get('OUTPUT_PATH', None) is None:
    app.config['OUTPUT_PATH'] = os.path.join(os.path.dirname(__file__), "..","output")
if not os.path.exists(app.config['OUTPUT_PATH']):
    os.makedirs(app.config['OUTPUT_PATH'])

# Create logging
if app.config.get('LOG_FILE') == True:
    import logging
    from logging import FileHandler
    file_handler = FileHandler('logs/larva_service.txt')
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