## Development Environment

Assumes you have:
* python >= 2.7.2
* MongoDB >= 1.8.2
* foreman (ruby gem)
* heroku (ruby gem)

### Install the requirements
    $ pip install -r requirements.rb

### Create an .env file with the following contents
    APPLICATION_SETTINGS=development.py
    SECRET_KEY=somethinglongandunique
    CELERY_BROKER=celery_broker_string

### Edit larva_service/development.py and larva_service/testing.py
    Add MongoDB connection information

### Start the local server
    $ foreman start

## Starting a Heroku instance

    $ heroku create --stack cedar NAME_OF_APP

    $ heroku config:add APPLICATION_SETTINGS=production.py
    $ heroku config:add SECRET_KEY=somethinglongandunique
    $ heroku config:add CELERY_BROKER=celery_broker_string

    $ heroku addons:add mongolab:starter
    $ git push heroku master
    $ heroku ps:scale web=1
