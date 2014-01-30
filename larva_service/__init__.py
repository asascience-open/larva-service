import os

from flask import Flask
from flask.ext.mongokit import MongoKit

import datetime

# Create application object
app = Flask(__name__)

app.config.from_object('larva_service.defaults')
app.config.from_envvar('APPLICATION_SETTINGS', silent=True)

# Setup RQ Dashboard
from rq_dashboard import RQDashboard
RQDashboard(app)

# Setup OUTPUT_PATH
if app.config.get('OUTPUT_PATH', None) is None:
    app.config['OUTPUT_PATH'] = os.path.join(os.path.dirname(__file__), "..", "output")
if not os.path.exists(app.config['OUTPUT_PATH']):
    os.makedirs(app.config['OUTPUT_PATH'])

# Create logging
if app.config.get('LOG_FILE') is True:
    import logging
    from logging import FileHandler
    file_handler = FileHandler('logs/larva_service.txt')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

# Create the Redis connection
import redis
from rq import Queue
redis_connection = redis.from_url(app.config.get("REDIS_URI"))
run_queue = Queue('runs', connection=redis_connection, default_timeout=604800)  # 1 week timeout
dataset_queue = Queue('datasets', connection=redis_connection, default_timeout=600)  # 10 min timeout
shoreline_queue = Queue('shorelines', connection=redis_connection, default_timeout=600)  # 10 min timeout

# Create the database connection
db = MongoKit(app)


# Create datetime jinja2 filter
def datetimeformat(value, format='%a, %b %d %Y at %I:%M%p'):
    if isinstance(value, datetime.datetime):
        return value.strftime(format)
    return value
app.jinja_env.filters['datetimeformat'] = datetimeformat


def timedeltaformat(starting, ending):
    if isinstance(starting, datetime.datetime) and isinstance(ending, datetime.datetime):
        return ending - starting
    return "unknown"
app.jinja_env.filters['timedeltaformat'] = timedeltaformat


def slugify(value):
    """
    Normalizes string, removes non-alpha characters, and converts spaces to hyphens.
    Pulled from Django
    """
    import unicodedata
    import re
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip())
    return unicode(re.sub('[-\s]+', '-', value))

# Import everything
import larva_service.views
import larva_service.models
import larva_service.tasks
