import os
import urlparse

mongolab_uri = os.environ.get('MONGOLAB_URI')
url = urlparse.urlparse(mongolab_uri)

# Database
MONGODB_HOST = url.hostname
MONGODB_PORT = url.port
MONGODB_USERNAME = url.username
MONGODB_PASSWORD = url.password
MONGODB_DATABASE = url.path[1:]

# Celery
BROKER_URL = os.environ.get('REDISTOGO_URL')
BROKER_POOL_LIMIT = 4

S3_BUCKET = "larvamap-production"