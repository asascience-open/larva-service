from larva_service import celery, app, db
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import json

@celery.task()
def calc(dataset_id):
    with app.app_context():

        # Save results back to Run
        dataset = db.Dataset.find_one( { '_id' : ObjectId(dataset_id) } )
        
        if dataset is None:
            return "No Dataset exists to update, aborting update process for ID %s" % dataset_id

        dataset.calc()
        dataset.updated = datetime.utcnow()
        dataset.save()

        # Do this again in 3 hours
        hours = 3
        seconds = hours * 60. * 60.
        results = calc.apply_async([dataset_id], countdown=seconds, queue='datasets')
        dataset.task_id = unicode(results.task_id)
        dataset.save()

        return "Successfully updated dataset %s (%s)" % (dataset_id, dataset.name)