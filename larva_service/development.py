DEBUG = True
LOG_FILE = True

# Database
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DATABASE = 'larvaservice_development'
MONGODB_USERNAME = 'larvamap'
MONGODB_PASSWORD = 'yourpassword'

# Celery
BROKER_URL = 'redis://localhost:6379/0'

S3_BUCKET = "larvamap-development"
