web: gunicorn app:app -b 0.0.0.0:$PORT -w 1
celery_datasets: celeryd -A larva_service.celery -l info -E -B -c 1 -Q datasets,default

# We are not going to run the "runs" workers on Heroku.
# They will be run on a seperate EC2 instance with sufficient resources
#celery_runs: celeryd -A larva_service.celery -l info -E -c 1 -Q runs
