DEBUG = True
LOG_FILE = True

USE_S3 = False
S3_BUCKET = "larvamap-test"
NON_S3_OUTPUT_URL = "http://localhost/lmfiles/"

BATHY_PATH = "/data/lm/bathy/ETOPO1_Bed_g_gmt4.grd"
OUTPUT_PATH = "/data/lm/output"
SHORE_PATH = "/data/lm/shore/global/10m_land.shp"

TESTING = True

import urlparse

# Database
MONGO_URI = "mongodb://larvamap:yourpassword@localhost:27017/larvaservice_testing"
url = urlparse.urlparse(MONGO_URI)
MONGODB_HOST = url.hostname
MONGODB_PORT = url.port
MONGODB_USERNAME = url.username
MONGODB_PASSWORD = url.password
MONGODB_DATABASE = url.path[1:]

# Redis
REDIS_URI = "redis://localhost:6379/1"
url = urlparse.urlparse(REDIS_URI)
REDIS_HOST = url.hostname
REDIS_PORT = url.port
REDIS_USERNAME = url.username
REDIS_PASSWORD = url.password
REDIS_DB = url.path[1:]
