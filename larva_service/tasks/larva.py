from larva_service import app, db, slugify
from flask import current_app
from time import sleep
from shapely.wkt import dumps, loads
import json
import pytz
import math
import os
import shutil
import multiprocessing, logging
from datetime import datetime
PROGRESS=15
logging.PROGRESS = PROGRESS
logging.addLevelName(PROGRESS, 'PROGRESS')
def progress(self, message, *args, **kws):
    if self.isEnabledFor(PROGRESS):
        self._log(PROGRESS, message, args, **kws)
logging.Logger.progress = progress

import threading
import collections

from paegan.transport.models.behavior import LarvaBehavior
from paegan.transport.models.transport import Transport
from paegan.transport.model_controller import ModelController

from paegan.logger.multi_process_logging import MultiProcessingLogHandler
from paegan.logger.progress_handler import ProgressHandler

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from bson.objectid import ObjectId

from rq import get_current_job

import time

def run(run_id):

    # Sleep to give the Run object enough time to save
    time.sleep(10)

    with app.app_context():
        from paegan.logger import logger

        job = get_current_job()

        output_path = os.path.join(current_app.config['OUTPUT_PATH'], run_id)
        temp_animation_path = os.path.join(current_app.config['OUTPUT_PATH'], "temp_images_" + run_id)

        shutil.rmtree(output_path, ignore_errors=True)
        os.makedirs(output_path)

        shutil.rmtree(temp_animation_path, ignore_errors=True)
        os.makedirs(temp_animation_path)

        # Set up Logger
        queue = multiprocessing.Queue(-1)
        
        # Close any existing handlers
        (hand.close() for hand in logger.handlers)
        # Remove any existing handlers
        logger.handlers = []
        logger.setLevel(logging.PROGRESS)
        handler = MultiProcessingLogHandler(os.path.join(output_path, '%s.log' % run_id), queue)
        handler.setLevel(logging.PROGRESS)
        formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(name)s - %(processName)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Progress stuff.  Hokey!
        progress_deque = collections.deque(maxlen=1)
        progress_handler = ProgressHandler(progress_deque)
        progress_handler.setLevel(logging.PROGRESS)
        logger.addHandler(progress_handler)

        e = threading.Event()

        def save_progress():
            while e.wait(5) != True:
                try:
                    record = progress_deque.pop()
                    if record == StopIteration:
                        break

                    job.meta["updated"] = record[0]
                    if record is not None and record[1] >= 0:
                        job.meta["progress"] = record[1]
                    if isinstance(record[2],unicode) or isinstance(record[2], str):
                        job.meta["message"] = record[2]

                    job.save()
                except IndexError:
                    pass
                except Exception:
                    raise
            return

        t = threading.Thread(name="ProgressUpdater", target=save_progress)
        t.daemon = True
        t.start()

        try:

            logger.progress((0, "Configuring model"))

            run = db.Run.find_one( { '_id' : ObjectId(run_id) } )
            if run is None:
                return "Failed to locate run %s. May have been deleted while task was in the queue?" % run_id

            geometry       = loads(run['geometry'])
            start_depth    = run['release_depth']
            num_particles  = run['particles']
            time_step      = run['timestep']
            num_steps      = int(math.ceil((run['duration'] * 24 * 60 * 60) / time_step))
            start_time     = run['start'].replace(tzinfo = pytz.utc)
            shoreline_path = run['shoreline_path'] or app.config.get("SHORE_PATH")
            shoreline_feat = run['shoreline_feature']

            # Set up output directory/bucket for run
            output_formats = ['Shapefile','NetCDF','Trackline']

            # Setup Models
            models = []
            if run['cached_behavior'] is not None and run['cached_behavior'].get('results', None) is not None:
                behavior_data = run['cached_behavior']['results'][0]
                l = LarvaBehavior(data=behavior_data)
                models.append(l)
            models.append(Transport(horizDisp=run['horiz_dispersion'], vertDisp=run['vert_dispersion']))


            # Setup ModelController
            model = ModelController(geometry=geometry, depth=start_depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=True, use_shoreline=True,
                time_chunk=run['time_chunk'], horiz_chunk=run['horiz_chunk'], time_method=run['time_method'], shoreline_path=shoreline_path, shoreline_feature=shoreline_feat, reverse_distance=1500)

            # Run the model
            cache_file = os.path.join(current_app.config['CACHE_PATH'], "hydro_" + run_id + ".cache")
            bathy_file = current_app.config['BATHY_PATH']
            
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
            
        except Exception as exception:
            logger.warn("Run FAILED, cleaning up and uploading log.")
            logger.warn(exception.message)
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
            logger.progress((99, "Uploading files to S3"))

            # Close the handler so we can upload the log file without a file lock
            (hand.close() for hand in logger.handlers)
            queue.put(StopIteration)
            # Break out of the progress loop
            e.set()

            for filename in os.listdir(output_path):
                outfile = os.path.join(output_path,filename)

                # Upload the outputfiles with the same as the run name
                name, ext = os.path.splitext(filename)
                new_filename = slugify(unicode(run['name'])) + ext

                k = Key(bucket)
                k.key = "output/%s/%s" % (run_id, new_filename)
                k.set_contents_from_filename(outfile)
                k.set_acl('public-read')
                result_files.append("%s/%s" % (base_s3_url, new_filename))
                os.remove(outfile)

            shutil.rmtree(output_path, ignore_errors=True)
            shutil.rmtree(temp_animation_path, ignore_errors=True)

            # Set output fields
            run.output = result_files
            run.ended = datetime.utcnow()
            run.compute()
            run.save()

            # Cleanup
            logger.removeHandler(handler)
            del formatter
            del handler
            del logger
            del model
            queue.close()

            job.meta["message"] = "Complete"
            job.save()
