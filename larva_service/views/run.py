from flask import render_template, redirect, url_for, request, flash, jsonify
from larva_service import app, db
from celery.task.control import revoke
from larva_service.tasks.larva import run as larva_run
import json
import pytz
from larva_service.models import remove_mongo_keys
from pymongo import DESCENDING

@app.route('/run', methods=['GET', 'POST'])
@app.route('/run.<string:format>', methods=['GET', 'POST'])
def run_larva_model(format=None):

    if format is None:
        format = 'html'

    if request.method == 'GET':
        run_details = request.args.get("config", None)
    elif request.method == 'POST':
        run_details = request.form.get("config", None)

    config_dict = None
    try:
        config_dict = json.loads(run_details.strip())
    except:
        message = "Could not decode parameters"
        if format == 'html':
            flash(message, 'error')
            return redirect(url_for('runs'))
        elif format == 'json':
            return jsonify( { 'results' : message } )

    run = db.Run()
    run.load_run_config(config_dict)
    run.save()

    # Pass in the Run ID to the task
    results = larva_run.delay(unicode(run['_id']))
    run.task_id = unicode(results.task_id)
    run.save()

    message = "Run created"
    if format == 'html':
        flash(message, 'success')
        return redirect(url_for('runs'))
    elif format == 'json':
        return jsonify( { 'results' : unicode(run['_id']) } )

@app.route('/runs/<ObjectId:run_id>/delete', methods=['GET','DELETE'])
@app.route('/runs/<ObjectId:run_id>/delete.<string:format>', methods=['GET','DELETE'])
def delete_run(run_id, format=None):
    if format is None:
        format = 'html'

    run = db.Run.find_one( { '_id' : run_id } )

    # Kill the Celery task
    revoke(run.task_id, terminate=True)

    run.delete()

    if format == 'json':
        return jsonify( { 'status' : "success" })
    else:
        flash("Run deleted")
        return redirect(url_for('runs'))

@app.route('/runs/clear', methods=['GET'])
def clear_runs():
    db.drop_collection("runs")
    return redirect(url_for('runs'))

@app.route('/runs', methods=['GET'])
@app.route('/runs.<string:format>', methods=['GET'])
def runs(format=None):
    if format is None:
        format = 'html'

    runs = db.Run.find().sort('created', DESCENDING)

    if format == 'html':
        return render_template('runs.html', runs=runs)
    elif format == 'json':
        jsond = []
        for run in runs:
            js = json.loads(run.to_json())
            remove_mongo_keys(js, extra=['output', 'cached_behavior'])
            js['_id'] = unicode(run._id)
            js['status'] = unicode(run.status())
            js['output'] = list(run.output_files())
            jsond.append(js)
        return jsonify( { 'results' : jsond } )
    else:
        flash("Reponse format '%s' not supported" % format)
        return redirect(url_for('runs'))

@app.route('/runs/<ObjectId:run_id>', methods=['GET'])
@app.route('/runs/<ObjectId:run_id>.<string:format>', methods=['GET'])
def show_run(run_id, format=None):
    if format is None:
        format = 'html'

    run = db.Run.find_one( { '_id' : run_id } )

    if format == 'html':
        markers = run.google_maps_coordinates()
        run_config = json.dumps(run.run_config(), sort_keys=True, indent=4)
        cached_behavior = json.dumps(run.cached_behavior, sort_keys=True, indent=4)
        output_files = run.output_files()
        return render_template('show_run.html', run=run, run_config=run_config, cached_behavior=cached_behavior, markers=markers)
    elif format == 'json':
        jsond = json.loads(run.to_json())
        remove_mongo_keys(jsond, extra=['output'])
        jsond['_id'] = unicode(run._id)
        jsond['status'] = unicode(run.status())
        jsond['output'] = list(run.output_files())
        return jsonify( jsond )
    else:
        flash("Reponse format '%s' not supported" % format)
        return redirect(url_for('runs'))

@app.route('/runs/<ObjectId:run_id>/status', methods=['GET'])
@app.route('/runs/<ObjectId:run_id>/status.<string:format>', methods=['GET'])
def status_run(run_id, format=None):
    if format is None:
        format = 'json'

    run = db.Run.find_one( { '_id' : run_id } )
    run_status = run.status()

    if format == 'json':
        return jsonify( { 'status' : run_status })
    else:
        flash("Reponse format '%s' not supported" % format)
        return redirect(url_for('runs'))

@app.route('/runs/<ObjectId:run_id>/run_config', methods=['GET'])
def run_config(run_id):
    run = db.Run.find_one( { '_id' : run_id } )
    return jsonify( run.run_config() )
