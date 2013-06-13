from flask import render_template, redirect, url_for, request, flash, jsonify
from larva_service import app, db, shoreline_queue
from larva_service.models.shoreline import Shoreline
from larva_service.tasks.shoreline import get_info
from larva_service.views.helpers import requires_auth
import json
import pytz
from larva_service.models import remove_mongo_keys
from pymongo import DESCENDING
from rq import cancel_job

@app.route('/shorelines', methods=['GET'])
@app.route('/shorelines.<string:format>', methods=['GET'])
def shorelines(format=None):
    if format is None:
        format = 'html'

    shorelines = db.Shoreline.find().sort('created', DESCENDING)

    if format == 'html':
        return render_template('shorelines.html', shorelines=shorelines)
    elif format == 'json':
        jsonsl = []
        for sl in shorelines:
            js = json.loads(sl.to_json())
            remove_mongo_keys(js)
            js['_id'] = unicode(sl._id)
            jsonsl.append(js)
        return jsonify( { 'results' : jsonsl } )
    else:
        flash("Response format '%s' not supported" % format)
        return redirect(url_for('shorelines'))

@app.route('/shoreline', methods=['POST'])
@requires_auth
def add_shoreline():
    shoreline = db.Shoreline()
    shoreline.name = request.form.get("name")
    shoreline.path = request.form.get("path")
    shoreline.feature_name = request.form.get("feature_name")
    shoreline.save()

    job = shoreline_queue.enqueue_call(func=get_info, args=(unicode(shoreline['_id']),))
    shoreline.task_id = unicode(job.id)
    shoreline.save()

    flash("Shoreline created", 'success')
    return redirect(url_for('shorelines'))

@app.route('/shorelines/<ObjectId:shoreline_id>', methods=['GET'])
@app.route('/shorelines/<ObjectId:shoreline_id>.<string:format>', methods=['GET'])
def show_shoreline(shoreline_id, format=None):
    if format is None:
        format = 'html'

    shoreline = db.Shoreline.find_one( { '_id' : shoreline_id } )

    if format == 'html':
        return render_template('show_shoreline.html', shoreline=shoreline)
    elif format == 'json':
        jsond = json.loads(shoreline.to_json())
        remove_mongo_keys(jsond) #destructive method
        jsond['_id'] = unicode(shoreline._id)
        return jsonify( jsond )
    else:
        flash("Reponse format '%s' not supported" % format)
        return redirect(url_for('shorelines'))

@app.route('/shorelines/<ObjectId:shoreline_id>/delete', methods=['GET'])
@app.route('/shorelines/<ObjectId:shoreline_id>/delete.<string:format>', methods=['GET'])
@requires_auth
def delete_shoreline(shoreline_id, format=None):
    if format is None:
        format = 'html'

    shoreline = db.Shoreline.find_one( { '_id' : shoreline_id } )
    cancel_job(shoreline.task_id)
    shoreline.delete()

    if format == 'json':
        return jsonify( { 'status' : "success" })
    else:
        flash("Shoreline deleted")
        return redirect(url_for('shorelines'))

@app.route('/shorelines/clear', methods=['GET'])
@requires_auth
def clear_shorelines():
    db.drop_collection("shorelines")
    return redirect(url_for('shorelines'))

