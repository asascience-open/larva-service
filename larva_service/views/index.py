from flask import render_template, redirect, url_for
from larva_service import app, db
from larva_service.tasks.larva import run
from larva_service.models.task import Task

@app.route('/', methods=['GET'])
def index():        
    tasks = db.Task.find()
    return render_template('index.html', tasks=tasks)

@app.route('/cleartasks', methods=['GET'])
def cleartasks():
    db.drop_collection("tasks")
    return redirect(url_for('index'))

@app.route('/runtask', methods=['GET'])
def runtask():
    results = run.delay(4,2)
    return redirect(url_for('index'))
