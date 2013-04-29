import json
import os
from flask.ext.mongokit import Document
from larva_service import app, db, redis_connection
from datetime import datetime
from shapely.geometry import Point
from shapely.wkt import loads
from paegan.cdm.dataset import CommonDataset
from shapely.geometry import box
from rq.job import Job

class Dataset(Document):
    __collection__ = 'datasets'
    use_dot_notation = True
    structure = {
        'name'              : unicode,  # Name of the dataset
        'starting'          : datetime, # URL to Behavior JSON
        'ending'            : datetime, # Save the contents of behavior URL
        'timestep'          : int,      # Model timestep, in seconds
        'location'          : unicode,  # DAP endpoint
        'bbox'              : unicode,  # WKT of the bounding box
        'geometry'          : unicode,  # WKT of the bounding polygon
        'variables'         : dict,     # dict of variables, including attributes
        'keywords'          : list,     # keywords pulled from global attributes of dataset
        'messages'          : list,     # Error messages
        'task_id'           : unicode,  # Task processing the dataset
        'created'           : datetime,
        'updated'           : datetime
    }
    default_values = {
                      'created': datetime.utcnow
                      }
                      
    def status(self):
        if Job.exists(self.task_id, connection=redis_connection):
            job = Job.fetch(self.task_id, connection=redis_connection)
            job.refresh()
            return job.status
        else:
            return "unknown"

    def calc(self):
        """
        Compute bounds for this dataset
        """
        try:
            nc = CommonDataset.open(self.location)

            query_var = nc.get_varname_from_stdname("eastward_sea_water_velocity")[0]

            # Set BBOX
            minx, miny, maxx, maxy = nc.getbbox(var=query_var)
            self.bbox = unicode(box(minx, miny, maxx, maxy).wkt)

            # Set Bounding Polygon
            # Bounding polygon is not implemented in Paegan yet
            #poly = nc.getboundingpolygon(var=query_var)
            #self.geometry = poly
            
            # Set Time bounds
            mintime, maxtime = nc.gettimebounds(var=query_var)
            self.starting = mintime
            self.ending = maxtime

            def clean(value):
                try:
                    str(type(value)).index("numpy")
                except:
                    return value
                else:
                    return value.tolist()

            
            cleaned_info = {}
            variables = nc.getvariableinfo()
            for k,v in variables.items():
                # Strip out numpy arrays into BSON encodable things.
                cleaned_var = { key:clean(value) for key,value in v.items() }
                cleaned_info[k] = cleaned_var

            self.variables = cleaned_info

        except:
            app.logger.warning("Could not calculate bounds for this dataset")
            raise

    def google_maps_coordinates(self):
        marker_positions = []
        if self.geometry:
            geo = loads(self.geometry)
        elif self.bbox:
            geo = loads(self.bbox)
        else:
            return marker_positions

        if isinstance(geo, Point):
            marker_positions.append((geo.coords[0][1], geo.coords[0][0]))
        else:
            for pt in geo.exterior.coords:
                # Google maps is y,x not x,y
                marker_positions.append((pt[1], pt[0]))

        return marker_positions

db.register([Dataset])