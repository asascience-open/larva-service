from flask import make_response, render_template
from larva_service import app, db, celery
import json
from celery.task.control import revoke

@app.route('/tasks', methods=['GET'])
@app.route('/tasks.<string:format>', methods=['GET'])
def tasks(format=None):

    try:
        nodes = celery.control.inspect()
    except Exception as e:
        app.logger.warn(e)
        nodes = None

    active = None
    scheduled = None
    waiting = None

    if nodes is not None:
        try:
            active = nodes.active()
        except Exception as e:
            app.logger.warn(e)
        
        try:
            scheduled = nodes.scheduled()
        except Exception as e:
            app.logger.warn(e)

        try:
            waiting = nodes.reserved()
        except Exception as e:
            app.logger.warn(e)

    if active is None:
        active = {}
    if scheduled is None:
        scheduled = {}
    if waiting is None:
        waiting = {}


    return render_template('tasks.html', active=active, scheduled=scheduled, waiting=waiting)
