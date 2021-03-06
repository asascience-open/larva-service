from larva_service import app, db, slugify
from flask import current_app
from shapely.wkt import loads
import tempfile
import pytz
import math
import os
import shutil
import multiprocessing
import logging
from datetime import datetime
from urlparse import urljoin

PROGRESS = 15
logging.PROGRESS = PROGRESS
logging.addLevelName(PROGRESS, 'PROGRESS')
def progress(self, message, *args, **kwargs):
    if self.isEnabledFor(PROGRESS):
        self._log(PROGRESS, message, args, **kwargs)
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
        shutil.rmtree(output_path, ignore_errors=True)
        os.makedirs(output_path)

        cache_path = os.path.join(current_app.config['CACHE_PATH'], run_id)
        shutil.rmtree(cache_path, ignore_errors=True)
        os.makedirs(cache_path)

        temp_animation_path = os.path.join(current_app.config['OUTPUT_PATH'], "temp_images_" + run_id)
        shutil.rmtree(temp_animation_path, ignore_errors=True)
        os.makedirs(temp_animation_path)

        # Set up Logger
        queue = multiprocessing.Queue(-1)

        f, log_file = tempfile.mkstemp(dir=cache_path, prefix=run_id, suffix=".log")
        os.close(f)

        # Close any existing handlers
        (hand.close() for hand in logger.handlers)
        # Remove any existing handlers
        logger.handlers = []
        logger.setLevel(logging.PROGRESS)
        handler = MultiProcessingLogHandler(log_file, queue)
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
            while e.wait(5) is not True:
                try:
                    record = progress_deque.pop()
                    if record == StopIteration:
                        break

                    job.meta["updated"] = record[0]
                    if record is not None and record[1] >= 0:
                        job.meta["progress"] = record[1]
                    if isinstance(record[2], unicode) or isinstance(record[2], str):
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

        model = None

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
            output_formats = ['Shapefile', 'NetCDF', 'Trackline']

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
            cache_file = os.path.join(cache_path, run_id + ".nc.cache")
            bathy_file = current_app.config['BATHY_PATH']

            model.run(run['hydro_path'], output_path=output_path, bathy=bathy_file, output_formats=output_formats, cache=cache_file, remove_cache=False, caching=run['caching'])

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

            logger.progress((99, "Processing output files"))
            # Close the handler so we can upload the log file without a file lock
            (hand.close() for hand in logger.handlers)
            queue.put(StopIteration)
            # Break out of the progress loop
            e.set()
            t.join()

            # Move logfile to output directory
            shutil.move(log_file, os.path.join(output_path, 'model.log'))

            # Move cachefile to output directory if we made one
            if run['caching']:
                shutil.move(cache_file, output_path)

            output_files = []
            for filename in os.listdir(output_path):
                outfile = os.path.join(output_path, filename)
                output_files.append(outfile)

            result_files = []
            base_access_url = current_app.config.get('NON_S3_OUTPUT_URL', None)
            # Handle results and cleanup
            if current_app.config['USE_S3'] is True:
                base_access_url = urljoin("http://%s.s3.amazonaws.com/output/" % current_app.config['S3_BUCKET'], run_id)
                # Upload results to S3 and remove the local copies
                conn = S3Connection()
                bucket = conn.get_bucket(current_app.config['S3_BUCKET'])

                for outfile in output_files:
                    # Don't upload the cache file
                    if os.path.basename(outfile) == os.path.basename(cache_file):
                        continue

                    # Upload the outfile with the same as the run name
                    _, ext = os.path.splitext(outfile)
                    new_filename = slugify(unicode(run['name'])) + ext

                    k = Key(bucket)
                    k.key = "output/%s/%s" % (run_id, new_filename)
                    k.set_contents_from_filename(outfile)
                    k.set_acl('public-read')
                    result_files.append(base_access_url + "/" + new_filename)
                    os.remove(outfile)

                shutil.rmtree(output_path, ignore_errors=True)

            else:
                for outfile in output_files:
                    result_files.append(urljoin(base_access_url, run_id) + "/" + os.path.basename(outfile))

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
