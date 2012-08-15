from flask import render_template, redirect, url_for, flash
from larva_service import app, db
from larva_service.models.task import Task
from larva_service.tasks.larva import add

@app.route('/queue', methods=['GET'])
def queue():        
    tasks = db.Task.find()
    flash("On queue page",  'info')
    return render_template('queue.html', tasks=tasks)

@app.route('/queue/clear', methods=['GET'])
def clear_queue():
    db.drop_collection("tasks")
    return redirect(url_for('queue'))

@app.route('/queue/add', methods=['GET'])
def add_to_queue():
    results = add.delay(4,2)
    return redirect(url_for('queue'))