DEBUG = True
TESTING = True
LOG_FILE = True

# Database
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DATABASE = 'larvaservice_testing'
MONGODB_USERNAME = 'larvamap'
MONGODB_PASSWORD = 'yourpassword'

# Celery
BROKER_URL = 'redis://localhost:6379/1'

S3_BUCKET = "larvamap-testing"