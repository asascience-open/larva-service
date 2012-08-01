from flask import render_template
from larva_service import app, db
from larva_service.tasks import run_model
from time import sleep
from larva_service.models.task import Task

@app.route('/', methods=['GET'])
def index():
    
    results = run_model.run_larva_model.delay(4, 2)
    sleep(2)
    app.logger.info(results.ready())

    tasks = db['tasks'].find()

    return render_template('index.html', tasks=tasks)