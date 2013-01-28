DEBUG = True
LOG_FILE = True

# Database
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DATABASE = 'larvaservice_development'
MONGODB_USERNAME = 'larvamap'
MONGODB_PASSWORD = 'yourpassword'

# Celery
S3_BUCKET = "larvamap-development"

BATHY_PATH = "/home/dev/Development/paegan/paegan/resources/bathymetry/ETOPO1_Bed_g_gmt4.grd"
CACHE_PATH = "/home/dev/Development/larva-service/cache"
OUTPUT_PATH = "/home/dev/Development/larva-service/output"
SHORE_PATH = "/home/dev/Development/paegan/paegan/resources/shoreline/westcoast/New_Land_Clean.shp"