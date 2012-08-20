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

    config_dict = None
    try:
        config_dict = json.loads(run_details)
    except:
        flash("Could not decode parameters", 'error')
        return redirect(url_for('runs'))

    run = db.Run()
    run.load_run_config(config_dict)
    results = larva_run.delay(run.to_json())
    run.task_id = unicode(results.task_id)
    run.save()
    flash("Run created", 'success')
    return redirect(url_for('runs'))

@app.route('/runs/clear', methods=['GET'])
def clear_runs():
    db.drop_collection("runs")
    return redirect(url_for('runs'))

@app.route('/runs', methods=['GET'])
def runs():
    runs = db.Run.find()
    return render_template('runs.html', runs=runs)

@app.route('/runs/<ObjectId:run_id>', methods=['GET'])
@app.route('/runs/<ObjectId:run_id>.<string:format>', methods=['GET'])
def show_run(run_id, format=None):
    run = db.Run.find_one( { '_id' : run_id } )
    run_config = json.dumps(run.run_config(), sort_keys=True, indent=4)
    return render_template('show_run.html', run=run, run_config=run_config)