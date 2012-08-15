from flask import render_template, redirect, url_for, request, flash
from larva_service import app, db
from larva_service.tasks.larva import run as larva_run
from larva_service.models.task import Task
import json
import pytz

@app.route('/run', methods=['GET', 'POST'])
def run_larva_model():

    if request.method == 'GET':
        run_details = request.args.get("config", None)
    elif request.method == 'POST':
        run_details = request.form.get("config", None)

    run = db.Run()
    print run_details
    if run_details is not None:
        run.load_run_config(json.loads(run_details))
        results = larva_run.delay(run.to_json())
        run.task_id = unicode(results.task_id)
        run.save()
    else:
        flash("No run configuration specified", 'error')

    return redirect(url_for('runs'))

@app.route('/runs/clear', methods=['GET'])
def clear_runs():
    db.drop_collection("runs")
    return redirect(url_for('runs'))

@app.route('/runs', methods=['GET'])
def runs():
    runs = db.Run.find()
    return render_template('runs.html', runs=runs)
