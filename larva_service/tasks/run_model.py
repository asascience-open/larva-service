from larva_service import celery

@celery.task
def add(x,y):
	return x+y

results = add.delay(4, 4)