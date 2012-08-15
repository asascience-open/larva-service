from flask.ext.mongokit import Document
from larva_service import db
from datetime import datetime
from celery.result import AsyncResult
import json
import urllib2
import pytz

class Run(Document):
    __collection__ = 'runs'
    use_dot_notation = True
    structure = {
       'behavior'           : unicode,  # URL to Behavior JSON
       'cached_behavior'    : dict,     # Save the contents of behavior URL
       'particles'          : int,
       'hydro_path'         : unicode,  # OPeNDAP or Local file path
       'geometry'           : unicode,  # WKT
       'start'              : datetime, # Drop in time
       'duration'           : int,      # Days
       'created'            : datetime,
       'task_id'            : unicode,
       'email'              : unicode   # Email of the person who ran the model
    }
    default_values = {'created': datetime.utcnow}

    def task(self):
        return AsyncResult(self.task_id)

    def status(self):
        return self.task().state

    def load_run_config(self, run):
        # Set the 1:1 relationship between the config and this object
        for key, value in run.iteritems():
            if key == 'start':
                self[key] = datetime.fromtimestamp(value / 1000, pytz.utc)
                continue
                
            self[key] = value

        if self.behavior:
            b = urllib2.urlopen(self.behavior)
            self.cached_behavior = json.loads(b.read())

db.register([Run])