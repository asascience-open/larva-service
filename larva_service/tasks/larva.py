from larva_service import celery
from time import sleep
from celery import current_task

@celery.task()
def add(x, y):
    return x+y

@celery.task()
def run(run_dict):
    print run_dict
    return 9+9