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