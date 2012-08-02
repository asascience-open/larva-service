from larva_service import celery
from time import sleep
from celery import current_task

@celery.task()
def run(x, y):
    return x+y