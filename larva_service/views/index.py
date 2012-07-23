from flask import render_template
from larva_service import app

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')