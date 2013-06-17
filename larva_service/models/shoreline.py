import json
import os
from flask.ext.mongokit import Document
from larva_service import app, db, redis_connection
from datetime import datetime
from shapely.geometry import Point
from shapely.wkt import loads
from paegan.transport.shoreline import Shoreline as PTShoreline
from shapely.geometry import box
from rq.job import Job

class Shoreline(Document):
    __collection__ = 'shorelines'
    use_dot_notation = True
    structure = {
        'name'              : unicode,  # Name of the shoreline
        'path'              : unicode,  # url to WFS server or file name on disk
        'feature_name'      : unicode,  # feature name in WFS server
        'title'             : unicode,  # title of the shoreline in WFS
        'spatialbuffer'     : float,
        'react_type'        : unicode,  # "reverse", "bounce", or other for no movement
        'bbox'              : unicode,  # WKT of the bounding box
        'geometry'          : unicode,  # WKT of the bounding polygon (unused currently)
        'task_id'           : unicode,  # id of import task
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

    def get_info(self):
        s = PTShoreline(path=self.path, feature_name=self.feature_name)
        caps = s.get_feature_type_info()

        if caps is not None:
            self.bbox  = unicode(caps['LatLongBoundingBox'].wkt)
            self.title = unicode(caps['Name'])

db.register([Shoreline])
