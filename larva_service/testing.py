DEBUG = True
TESTING = True
LOG_FILE = True

# Database
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DATABASE = 'larvaservice_testing'
MONGODB_USERNAME = 'celery'
MONGODB_PASSWORD = 'yourpassword'

# Celery
BROKER_URL = "mongodb://%s:%s@%s:%s/larvaservice_messaging" % (MONGODB_USERNAME, MONGODB_PASSWORD, MONGODB_HOST, MONGODB_PORT)
