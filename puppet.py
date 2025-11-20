#!/home/jack/miniconda3/envs/PY39/bin/python

from flask import Flask, render_template, send_from_directory
from icecream import ic
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    ic("Serving puppet.html from templates")
    return render_template('puppet.html')

# Optional route to serve static files manually if needed
@app.route('/static/<path:filename>')
def static_files(filename):
    ic(f"Serving static file: {filename}")
    return send_from_directory('static', filename)

if __name__ == '__main__':
    ic("App started")
    app.run(host='0.0.0.0', port=5600, debug=True)
