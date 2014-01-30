## Development Environment

Assumes you have:
* python >= 2.7.2
* MongoDB >= 1.8.2 (running)
* foreman (ruby gem)
* redis (running)

### Install the requirements
    $ pip install -r requirements.txt

### Create an .env file with the following contents
    APPLICATION_SETTINGS=development.py
    SECRET_KEY='supersecretkeysupersuper'
    # Omit this to disable logging to a file.
    # Setting it to any value will enable logging to a file.
    LOG_FILE=yes
    MONGO_URI="mongodb://localhost:27017/larvaservice_development"
    REDIS_URI="redis://localhost:6379/0"
    # AWS account to upload results to
    AWS_ACCESS_KEY_ID=KEY
    AWS_SECRET_ACCESS_KEY=SECRET
    WEB_PASSWORD=WHATEVER_YOU_WANT

### Edit the .env file
    With your endpoints/passwords/whatevs

### Edit development.py and testing.py 
    With paths to the following:
    BATHY_PATH = "somewhere/ETOPO1_Bed_g_gmt4.grd"
    OUTPUT_PATH = "folder/somewhere"
    SHORE_PATH = "somewhere/New_Land_Clean.shp"

### Start the local server
    $ foreman start
