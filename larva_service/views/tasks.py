from flask import make_response, render_template
from larva_service import app, db, celery
import json

@app.route('/tasks', methods=['GET'])
@app.route('/tasks.<string:format>', methods=['GET'])
def tasks(format=None):

    try:
        nodes = celery.control.inspect()
    except Exception as e:
        app.logger.warn(e)
        nodes = None

    active = {}
    scheduled = {}
    waiting = {}

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

    return render_template('tasks.html', active=active, scheduled=scheduled, waiting=waiting)
