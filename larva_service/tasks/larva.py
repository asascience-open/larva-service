from larva_service import app, db
from flask import current_app
from time import sleep
from shapely.wkt import dumps, loads
import json
import pytz
import math
import os
import shutil
import multiprocessing, logging

from paegan.transport.models.behavior import LarvaBehavior
from paegan.transport.models.transport import Transport
from paegan.transport.model_controller import ModelController

from paegan.logging.multi_process_logging import MultiProcessingLogHandler

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from bson.objectid import ObjectId

from rq import get_current_job

def run(run_id):

    with app.app_context():

        job = get_current_job()

        job.meta["progress"] = 0
        job.meta["message"] = "Setting up output directories"
        job.save()
        output_path = os.path.join(current_app.config['OUTPUT_PATH'], run_id)
        temp_animation_path = os.path.join(current_app.config['OUTPUT_PATH'], "temp_images_" + run_id)

        shutil.rmtree(output_path, ignore_errors=True)
        os.makedirs(output_path)

        shutil.rmtree(temp_animation_path, ignore_errors=True)
        os.makedirs(temp_animation_path)

        
        job.meta["message"] = "Setting up log file"
        job.save()
        # Set up Logger
        queue = multiprocessing.Queue(-1)
        logger = multiprocessing.get_logger()
        # Close any existing handlers
        (hand.close() for hand in logger.handlers)
        # Remove any existing handlers
        logger.handlers = []
        logger.setLevel(logging.INFO)
        handler = MultiProcessingLogHandler(os.path.join(output_path, '%s.log' % run_id), queue)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(name)s - %(processName)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        try:

            job.meta["message"] = "Configuring model"
            job.save()

            run = db.Run.find_one( { '_id' : ObjectId(run_id) } )
            if run is None:
                return "Failed to locate run %s. May have been deleted while task was in the queue?" % run_id

            geometry = loads(run['geometry'])
            start_depth = run['release_depth']
            num_particles = run['particles']
            time_step = run['timestep']
            num_steps = int(math.ceil((run['duration'] * 24 * 60 * 60) / time_step))
            start_time = run['start'].replace(tzinfo=pytz.utc)

            # Set up output directory/bucket for run
            output_formats = ['Shapefile','NetCDF','Trackline']

            # Setup Models
            models = []
            if run['cached_behavior'] is not None and run['cached_behavior'].get('results', None) is not None:
                behavior_data = run['cached_behavior']['results'][0]
                l = LarvaBehavior(data=behavior_data)
                models.append(l)
            models.append(Transport(horizDisp=run['horiz_dispersion'], vertDisp=run['vert_dispersion']))

            shoreline_path = current_app.config.get("SHORE_PATH", None)

            # Setup ModelController
            model = ModelController(geometry=geometry, depth=start_depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=True, use_shoreline=True,
                time_chunk=run['time_chunk'], horiz_chunk=run['horiz_chunk'], time_method=run['time_method'], shoreline_path=shoreline_path)

            # Run the model
            cache_file = os.path.join(current_app.config['CACHE_PATH'], "hydro_" + run_id + ".cache")
            bathy_file = current_app.config['BATHY_PATH']
            

            job.meta["message"] = "Running model"
            job.save()
            model.run(run['hydro_path'], output_path=output_path, bathy=bathy_file, output_formats=output_formats, cache=cache_file, remove_cache=False)

            # Move cache file to output directory so it gets uploaded to S3
            # How about not.  These can be huge.
            #try:
            #    shutil.move(cache_file, output_path)
            #except (IOError, OSError):
            #    # The cache file was probably never written because the model failed
            #    logger.info("No cache file from model exists")
            #    pass
            try:
                os.remove(cache_file)
            except (IOError, OSError):
                logger.info("No cache file from model exists")

            # Skip creating movie output_path
            """
            from paegan.viz.trajectory import CFTrajectory
            
            logger.info("Creating animation...")
            for filename in os.listdir(output_path):
                if os.path.splitext(filename)[1][1:] == "nc":
                    # Found netCDF file
                    netcdf_file = os.path.join(output_path,filename)
                    traj = CFTrajectory(netcdf_file)
                    success = traj.plot_animate(os.path.join(output_path,'animation.avi'), temp_folder=temp_animation_path, bathy=app.config['BATHY_PATH'])
                    if not success:
                        logger.info("Could not create animation")
                    else:
                        logger.info("Animation saved")
            """
            job.meta["outcome"] = "success"
            job.save()
            return "Successfully ran %s" % run_id
            
        except Exception:
            logger.warn("Run FAILED, cleaning up and uploading log.")
            job.meta["outcome"] = "failed"
            job.save()
            raise

        finally:

            # Handle results and cleanup
            result_files = []
            base_s3_url = "http://%s.s3.amazonaws.com/output/%s" % (current_app.config['S3_BUCKET'], run_id)
            # Upload results to S3 and remove the local copies
            conn = S3Connection()
            bucket = conn.get_bucket(current_app.config['S3_BUCKET'])
            logger.info("Uploading files to to S3...")

            # Close the handler so we can upload the log file without a file lock
            (hand.close() for hand in logger.handlers)
            queue.put(StopIteration)

            job.meta["message"] = "Uploading results to S3"
            job.save()
            for filename in os.listdir(output_path):
                outfile = os.path.join(output_path,filename)
                k = Key(bucket)
                k.key = "output/%s/%s" % (run_id, filename)
                k.set_contents_from_filename(outfile)
                k.set_acl('public-read')
                result_files.append("%s/%s" % (base_s3_url, filename))
                os.remove(outfile)

            shutil.rmtree(output_path, ignore_errors=True)
            shutil.rmtree(temp_animation_path, ignore_errors=True)

            # Set output fields
            run.output = result_files
            run.compute()
            run.save()

            job.meta["message"] = "Cleaning up"
            job.save()
            # Cleanup
            logger.removeHandler(handler)
            del formatter
            del handler
            del logger
            del model
            queue.close()

            job.meta["progress"] = 100
            job.meta["message"] = "Complete"
            job.save()