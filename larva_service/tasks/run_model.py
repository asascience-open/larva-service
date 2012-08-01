from larva_service import celery
from time import sleep

@celery.task()
def run_larva_model(behavior_parameters, run_parameters):
    return behavior_parameters + run_parameters