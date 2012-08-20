from flask.ext.mongokit import Document
from larva_service import db
from datetime import datetime
from celery.result import AsyncResult
import json
import urllib2
import pytz
import calendar

class Run(Document):
    __collection__ = 'runs'
    use_dot_notation = True
    structure = {
       'behavior'           : unicode,  # URL to Behavior JSON
       'cached_behavior'    : dict,     # Save the contents of behavior URL
       'particles'          : int,      # Number of particles to force
       'hydro_path'         : unicode,  # OPeNDAP or Local file path
       'geometry'           : unicode,  # WKT
       'release_depth'      : float,    # Release depth
       'start'              : datetime, # Release in time
       'duration'           : int,      # Days
       'timestep'           : int,      # In seconds, the timestep between calculations
       'horiz_dispersion'   : float,    # Horizontal dispersion, in m/s
       'vert_dispersion'    : float,    # Horizontal dispersion, in m/s
       'time_chunk'         : int,
       'horiz_chunk'        : int,
       'created'            : datetime,
       'task_id'            : unicode,
       'email'              : unicode   # Email of the person who ran the model
    }
    default_values = {
                      'created': datetime.utcnow,
                      'time_chunk': 2,
                      'horiz_chunk': 2
                      }

    def task(self):
        return AsyncResult(self.task_id)

    def status(self):
        return self.task().state

    def run_config(self):

        skip_keys = ['_id','cached_behavior','created','task_id']
        d = {}
        for key,value in self.iteritems():
            try:
                skip_keys.index(key)
                pass
            except:
                # Not found, so proceed
                if key == 'start':
                    d[key] = calendar.timegm(value.utctimetuple()) * 1000
                else:
                    d[key] = value

        return d

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