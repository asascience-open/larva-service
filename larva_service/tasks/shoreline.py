from bson.objectid import ObjectId
from datetime import datetime
import time
from larva_service import app, db, dataset_queue

def get_info(shoreline_id):

    with app.app_context():

        # Save results back to Run
        shoreline = db.Shoreline.find_one( { '_id' : ObjectId(shoreline_id) } )

        if shoreline is None:
            return "No Shoreline exists to update, aborting update process for ID %s" % shoreline_id

        shoreline.get_info()
        shoreline.updated = datetime.utcnow()

        shoreline.save()

