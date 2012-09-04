web: gunicorn app:app -b 0.0.0.0:$PORT -w 2
celery_datasets: celeryd -A larva_service.celery -l info -B -E -c 1 -Q datasets,default
celery_runs: celeryd -A larva_service.celery -l info -E -c 1 -Q runs
celery_flower: celery flower --port=8080 --broker=$BROKER_URL
