from flask import make_response, render_template
from larva_service import app, db, celery
import json

@app.route('/tasks', methods=['GET'])
@app.route('/tasks.<string:format>', methods=['GET'])
def tasks(format=None):
    nodes = celery.control.inspect()

    try:
    	active = nodes.active()
    except:
    	active = {}
    
    try:
    	scheduled = nodes.scheduled()
    except:
    	scheduled = {}

    try:
    	waiting = nodes.reserved()
    except:
    	waiting = {}

    return render_template('tasks.html', active=active, scheduled=scheduled, waiting=waiting)
