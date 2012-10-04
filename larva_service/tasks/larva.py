from larva_service import celery, app, db
from time import sleep
from celery import current_task
from shapely.wkt import dumps, loads
import json
import pytz
from datetime import datetime
import math
import os
import shutil
import multiprocessing, logging

from paegan.transport.models.behavior import LarvaBehavior
from paegan.transport.models.transport import Transport
from paegan.transport.model_controller import ModelController

from paegan.logging.multi_process_logging import MultiProcessingLogHandler

from paegan.viz.trajectory import CFTrajectory

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from bson.objectid import ObjectId

@celery.task()
def run(run_dict):
    
    try:
        data = json.loads(run_dict)

        # Mongo style export to JSON
        run_id = data['_id']['$oid']

        geometry = loads(data['geometry'])
        start_depth = data['release_depth']
        num_particles = data['particles']
        time_step = data['timestep']
        num_steps = int(math.ceil((data['duration'] * 24 * 60 * 60) / time_step))
        start_time = datetime.fromtimestamp(data['start'] / 1000., pytz.utc)

        # Set up output directory/bucket for run
        output_formats = ['Shapefile','NetCDF','Trackline']

        output_path = os.path.join(app.config['OUTPUT_PATH'], run_id)
        shutil.rmtree(output_path, ignore_errors=True)
        os.makedirs(output_path)

        # Set up Logger
        logger = multiprocessing.get_logger()
        logger.setLevel(logging.INFO)
        handler = MultiProcessingLogHandler(os.path.join(output_path, '%s.log' % run_id))
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(name)s - %(processName)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Setup Models
        models = []
        if data['cached_behavior'] is not None and data['cached_behavior'].get('results', None) is not None:
            behavior_data = data['cached_behavior']['results'][0]
            l = LarvaBehavior(data=behavior_data)
            models.append(l)
        models.append(Transport(horizDisp=data['horiz_dispersion'], vertDisp=data['vert_dispersion']))

        # Setup ModelController
        model = ModelController(geometry=geometry, depth=start_depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=data['time_chunk'], horiz_chunk=data['horiz_chunk'], time_method=data['time_method'])

        # Run the model
        cache_file = os.path.join(app.config['CACHE_PATH'], "hydro_" + run_id + ".cache")
        model.run(data['hydro_path'], output_path=output_path, output_formats=output_formats, cache=cache_file, remove_cache=False)

        # Move cache file to output directory so it gets uploaded to S3
        try:
            shutil.move(cache_file, output_path)
        except:
            # The cache file was probably never written because the model failed
            logger.info("No cache file from model exists")
            pass

        # Create movie output
        for filename in os.listdir(output_path):
            if os.path.splitext(filename)[1][1:] == "nc":
                # Found netCDF file
                netcdf_file = os.path.join(output_path,filename)
                traj = CFTrajectory(netcdf_file)
                success = traj.plot_animate(os.path.join(output_path,'animation.avi'), bathy=app.config['BATHY_PATH'])
                if not success:
                    logger.info("Could not create animation")
                else:
                    logger.info("Animation saved")

        # Handle results
        result_files = []
        base_s3_url = "http://%s.s3.amazonaws.com/output/%s" % (app.config['S3_BUCKET'], run_id)
        # Upload results to S3 and remove the local copies
        conn = S3Connection()
        bucket = conn.get_bucket(app.config['S3_BUCKET'])
        for filename in os.listdir(output_path):
            outfile = os.path.join(output_path,filename)
            logger.info("Uploading %s to S3" % outfile)
            k = Key(bucket)
            k.key = "output/%s/%s" % (run_id, filename)
            k.set_contents_from_filename(outfile)
            k.set_acl('public-read')
            result_files.append("%s/%s" % (base_s3_url, filename))
            os.remove(outfile)

        shutil.rmtree(output_path, ignore_errors=True)

        with app.app_context():
            # Save results back to Run
            the_run = db.Run.find_one( { '_id' : ObjectId(run_id) } )
            if the_run is None:
                return "Failed to run %s" % run_id

            the_run.output = result_files
            the_run.compute()
            the_run.save()
            return "Successfully ran %s" % run_id

        del model
        handler.close()
        logger.shutdown()
        
    except:
        raise