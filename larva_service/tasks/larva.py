from larva_service import celery
from time import sleep
from celery import current_task
from shapely.wkt import dumps, loads
import json
import pytz
from datetime import datetime
import math
import os

from paegan.transport.models.behavior import LarvaBehavior
from paegan.transport.models.transport import Transport
from paegan.transport.model_controller import ModelController

@celery.task()
def run(run_dict):

    data = json.loads(run_dict)

    geometry = loads(data['geometry'])
    start_depth = data['release_depth']
    num_particles = data['particles']
    time_step = data['timestep']
    num_steps = int(math.ceil((data['duration'] * 24 * 60 * 60) / time_step))
    start_time = datetime.fromtimestamp(data['start'] / 1000., pytz.utc)

    models = []

    if data['cached_behavior'] is not None:
        behavior_data = data['cached_behavior']['results'][0]
        l = LarvaBehavior(data=behavior_data)
        models.append(l)

    models.append(Transport(horizDisp=data['horiz_dispersion'], vertDisp=data['vert_dispersion']))

    model = ModelController(geometry=geometry, depth=start_depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=False, use_shoreline=True,
        time_chunk=data['time_chunk'], horiz_chunk=data['horiz_chunk'])

    model.run(data['hydro_path'], cache=os.path.join(os.path.dirname(__file__), '..', '..', 'cache'))
