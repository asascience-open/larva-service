from flask import Flask
from flask.ext.mongokit import MongoKit
import os

# Create application object
app = Flask(__name__)
app.config.from_object('larva_service.default')
app.config.from_envvar('APPLICATION_SETTINGS', silent=True)

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
