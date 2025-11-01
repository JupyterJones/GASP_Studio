#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
from icecream import ic

app = Flask(__name__)

IMAGE_FOLDER = "static/images"
JSON_FOLDER = "layouts"
APP_PORT = 5400
# Ensure layouts folder exists
if not os.path.exists(JSON_FOLDER):
    os.makedirs(JSON_FOLDER)

# -----------------------
# JSON Layout helpers
# -----------------------
def get_next_layout_file():
    existing = [f for f in os.listdir(JSON_FOLDER) if f.startswith("layout") and f.endswith(".json")]
    numbers = [int(f.replace("layout","").replace(".json","")) for f in existing if f.replace("layout","").replace(".json","").isdigit()]
    next_num = max(numbers)+1 if numbers else 1
    return os.path.join(JSON_FOLDER, f"layout{next_num}.json")

def load_layout(filename):
    path = os.path.join(JSON_FOLDER, filename)
    if os.path.exists(path):
        with open(path,"r") as f:
            data = json.load(f)
            ic(f"Loaded layout {filename}: {data}")
            return data
    return {}

def save_layout(filename, data):
    path = os.path.join(JSON_FOLDER, filename)
    with open(path,"w") as f:
        json.dump(data,f,indent=4)
        ic(f"Saved layout {filename}: {data}")

# -----------------------
# Routes
# -----------------------
@app.route("/")
def index():
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith((".png",".jpg",".gif"))]
    # Load latest layout if exists
    existing = sorted([f for f in os.listdir(JSON_FOLDER) if f.startswith("layout") and f.endswith(".json")])
    positions = load_layout(existing[-1]) if existing else {}
    return render_template("editor.html", images=images, positions=positions, layout_file=(existing[-1] if existing else ""))

@app.route("/save_positions", methods=["POST"])
def save():
    data = request.json
    ic(f"Received positions: {data}")
    filename = get_next_layout_file()
    save_layout(filename, data)
    return jsonify({"status":"ok","file":filename})

@app.route("/layouts")
def list_layouts():
    layouts = sorted([f for f in os.listdir(JSON_FOLDER) if f.endswith(".json")])
    return jsonify(layouts)

@app.route("/layouts/<filename>")
def serve_layout(filename):
    return send_from_directory(JSON_FOLDER, filename)

@app.route("/play")
def play():
    layouts = sorted([f for f in os.listdir(JSON_FOLDER) if f.endswith(".json")])
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith((".png",".jpg",".gif"))]
    return render_template("play.html", layouts=layouts, images=images)

# -----------------------
# Run server
# -----------------------
if __name__ == '__main__':

    ic(f"App starting on http://localhost:{APP_PORT}")
    # debug=True for development only
    app.run(host="0.0.0.0", port=APP_PORT, debug=True)
