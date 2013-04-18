import urlparse

DEBUG = True
TESTING = True
LOG_FILE = True

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

S3_BUCKET = "larvamap-test"

BATHY_PATH = "/data/lm/bathy/ETOPO1_Bed_g_gmt4.grd"
CACHE_PATH = "/data/lm/cache"
OUTPUT_PATH = "/data/lm/output"
SHORE_PATH = "/home/dev/Development/paegan/paegan/resources/shoreline/global/10m_land.shp"