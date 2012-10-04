from flask.ext.mongokit import Document
from larva_service import db, app
from datetime import datetime
from celery.result import AsyncResult
import json
import urllib2
import pytz
import os
import calendar
from urlparse import urlparse
import mimetypes
from shapely.geometry import Point, Polygon, asShape
import geojson
from shapely.wkt import loads

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
       'time_method'        : unicode,  # Time method, 'nearest' or 'interp'
       'created'            : datetime,
       'task_id'            : unicode,
       'email'              : unicode,   # Email of the person who ran the model
       'output'             : list,
       'trackline'          : unicode
    }
    default_values = {
                      'created': datetime.utcnow,
                      'time_chunk': 2,
                      'horiz_chunk': 2
                      }

    def compute(self):
        """
        Add any metadata to this object from the model run output
        """
        try:
            self.set_trackline()
        except:
            app.logger.warning("Could no compute (cache) model run results locally")

    def set_trackline(self):
        if self.trackline is None:
            for filepath in self.output:
                if os.path.basename(filepath) == "trackline.geojson":
                    # Get trackline.geojson and cache locally
                    t = urllib2.urlopen(filepath)
                    self.trackline = unicode(asShape(geojson.loads(t.read())).wkt)
        return self.trackline

    def task(self):
        return AsyncResult(self.task_id)

    def result(self):
        return self.task().result

    def status(self):
        return self.task().state

    def google_maps_coordinates(self):
        marker_positions = []
        if self.geometry:
            geo = loads(self.geometry)
            # Always make a polygon
            if isinstance(geo, Point):
                marker_positions.append((geo.coords[0][1], geo.coords[0][0]))
            else:
                for pt in geo.exterior.coords:
                    # Google maps is y,x not x,y
                    marker_positions.append((pt[1], pt[0]))

        return marker_positions

    def get_file_key_and_path(self, file_path):
        path = urlparse(file_path).path
        name, ext = os.path.splitext(path)

        file_type = "Unknown (%s)" % ext
        if ext == ".zip":
            if name.find('shp') != -1:
                file_type = "Shapefile"
            else:
                file_type = "Zipfile"
        elif ext == ".nc":
            file_type = "NetCDF"
        elif ext == ".cache":
            file_type = "Forcing Data"
        elif ext == ".json":
            file_type = "JSON"
        elif ext == ".geojson":
            file_type = "Trackline (GeoJSON)"
        elif ext == ".avi":
            file_type = "Animation"
        elif ext == ".log":
            file_type = "Logfile"

        return { file_type : file_path }

    def output_files(self):
        return (self.get_file_key_and_path(file_path) for file_path in self.output)

    def run_config(self):

        skip_keys = ['_id','cached_behavior','created','task_id','output','trackline']
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
                
            if key == 'release_depth' or key == 'horiz_dispersion' or key == 'vert_dispersion':
                self[key] = float(value)
                continue

            self[key] = value

        if self.behavior:
            try:
                b = urllib2.urlopen(self.behavior)
                self.cached_behavior = json.loads(b.read())
            except:
                pass

db.register([Run])