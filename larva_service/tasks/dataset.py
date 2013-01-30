from bson.objectid import ObjectId
from datetime import datetime
import time
from larva_service import app, db, dataset_queue

def calc(dataset_id):

    with app.app_context():

        # Save results back to Run
        dataset = db.Dataset.find_one( { '_id' : ObjectId(dataset_id) } )
        
        if dataset is None:
            return "No Dataset exists to update, aborting update process for ID %s" % dataset_id

        dataset.calc()
        dataset.updated = datetime.utcnow()

        # Poor man's scheduler, until rq supports scheduling
        # Sleep for 5 minutes to prevent crashing the DAP servers
        time.sleep(300)

        # And then do it again
        job = dataset_queue.enqueue_call(func=calc, args=(dataset_id,))
        dataset.task_id = unicode(job.id)
        dataset.save()

        return "Scheduled %s (%s)" % (dataset_id, dataset.name)