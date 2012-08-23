## Development Environment

Assumes you have:
* python >= 2.7.2
* MongoDB >= 1.8.2
* foreman (ruby gem)
* heroku (ruby gem)
* redis (running)

### Setup Mongo user for results
    $ mongo
    > use admin
    > db.addUser('admin', 'adminpassword')
    > db.auth('admin', 'adminpassword')
    > use larvamap_development
    > db.addUser("larvamap","yourpassword")
    > use larvamap_testing
    > db.addUser("larvamap","yourpassword")
    > exit

### Install the requirements
    $ pip install -r requirements.rb

### Create an .env file with the following contents
    APPLICATION_SETTINGS=development.py
    SECRET_KEY=somethinglongandunique
    LOG_FILE=yes
    AWS_ACCESS_KEY_ID=yourkey
    AWS_SECRET_ACCESS_KEY=yoursecret

### Edit larva_service/development.py and larva_service/testing.py
    Add MongoDB connection information
    Add Redis URL as BROKER_URL

### Start the local server
    $ foreman start

## Starting a Heroku instance

    $ heroku create --stack cedar NAME_OF_APP

    $ heroku config:add APPLICATION_SETTINGS=production.py
    $ heroku config:add SECRET_KEY=somethinglongandunique
    $ heroku config:add AWS_ACCESS_KEY_ID=yourkey
    $ heroku config:add AWS_SECRET_ACCESS_KEY=yoursecret

    $ heroku addons:add mongolab:starter
    $ heroku addons:add redistogo:nano
    $ git push heroku master
    $ heroku ps:scale web=1 celeryd=1
