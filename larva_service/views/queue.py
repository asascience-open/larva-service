from flask import render_template, redirect, url_for, flash
from larva_service import app, db
from larva_service.models.task import Task


@app.route('/queue', methods=['GET'])
def queue():        
    tasks = db.Task.find()
    return render_template('queue.html', tasks=tasks)

@app.route('/queue/clear', methods=['GET'])
def clear_queue():
    db.drop_collection("tasks")
    return redirect(url_for('queue'))

@app.route('/queue/<string:task_id>', methods=['GET'])
def show_task(task_id):
    task = db.Task.find_one( { '_id' : task_id } )
    return render_template('show_task.html', task=task)

