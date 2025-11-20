#!/usr/bin/env python3
# app.py
from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string
import os
from icecream import ic

app = Flask(__name__)

# -----------------------------
# Configuration
# -----------------------------
STATIC_DIR = os.path.join(os.getcwd(), "static")

# Filenames exactly as used by your animation JS
PART_FILES = {
    "torso": "torso.png",
    "head": "head.png",
    "upperArmL": "uarml.png",
    "lowerArmL": "larml.png",
    "upperArmR": "uarmr.png",
    "lowerArmR": "larmr.png",
    "upperLegL": "ulegl.png",
    "lowerLegL": "llegl.png",
    "upperLegR": "ulegr.png",
    "lowerLegR": "llegr.png",
    "footL": "footl.png",
    "footR": "footr.png",
    "background": "back512.jpg"
}

# Ensure static dir exists before app starts
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
    ic("Created static directory:", STATIC_DIR)

# -----------------------------
# Templates
# -----------------------------

INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Puppet Parts — Upload</title>
  <style>
    body{background:#0f0f12;color:#eee;font-family:Arial;margin:30px;}
    .container{max-width:900px;margin:auto;}
    .header{display:flex;justify-content:space-between;align-items:center;}
    .parts{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-top:18px;}
    .part{background:#17171a;padding:12px;border-radius:8px;border:1px solid #2b2b2f;}
    .part h4{margin:0 0 8px 0;font-size:16px;}
    .preview{max-width:220px;max-height:160px;border-radius:6px;border:1px solid #333;display:block;margin-bottom:8px;}
    form{display:flex;gap:8px;align-items:center;}
    input[type=file]{flex:1;}
    button{background:#2d9c57;color:white;padding:8px 12px;border-radius:6px;border:0;cursor:pointer;}
    a { color:#69a6ff; text-decoration:none; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Puppet Parts Upload</h1>
      <div>
        <a href="{{ url_for('animation') }}">View Animation</a> &nbsp; | &nbsp;
        <a href="{{ url_for('index') }}">Refresh</a>
      </div>
    </div>

    <p>Upload an image to replace a single part. Each part has its own upload form. Filenames are saved exactly as shown and will overwrite the file in <code>/static</code>.</p>

    <div class="parts">
      {% for key, filename in PART_FILES.items() %}
      <div class="part">
        <h4>{{ key }} &rarr; <small>{{ filename }}</small></h4>
        <img src="/static/{{ filename }}" class="preview" onerror="this.style.display='none'">
        <form action="{{ url_for('upload_part', part_name=key) }}" method="POST" enctype="multipart/form-data">
          <input type="file" name="file" accept="image/png,image/jpeg" required>
          <button type="submit">Upload {{ key }}</button>
        </form>
      </div>
      {% endfor %}
    </div>
  </div>
</body>
</html>
"""

# This is the full working animation HTML/JS you provided earlier (kept intact and served at /animation).
ANIMATION_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Walking Puppet Loop with Background</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js"></script>
<style>
body {
    margin: 0;
    background: #111;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}
canvas {
    background: #222;
}
</style>
</head>
<body>
<canvas id="canvas" width="512" height="600"></canvas>

<script>
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

// --- Global scale factor ---
const scale = .5; // adjust overall puppet size

// --- Background image ---
const bg = new Image();
bg.src = "/static/back512.jpg"; // <-- your background image in static folder
let bgLoaded = false;
bg.onload = () => bgLoaded = true;

// --- Load images ---
const parts = {};

const partFiles = {
  torso: '/static/torso.png',
  head: '/static/head.png',
  upperArmL: '/static/uarml.png',
  lowerArmL: '/static/larml.png',
  upperArmR: '/static/uarmr.png',
  lowerArmR: '/static/larmr.png',
  upperLegL: '/static/ulegl.png',
  lowerLegL: '/static/llegl.png',
  upperLegR: '/static/ulegr.png',
  lowerLegR: '/static/llegr.png',
  footL: '/static/footl.png',
  footR: '/static/footr.png'
};

let loaded = 0;
const totalParts = Object.keys(partFiles).length;

for (let key in partFiles) {
  parts[key] = new Image();
  parts[key].src = partFiles[key];
  parts[key].onload = () => {
    loaded++;
    if (loaded === totalParts) init();
  };
  parts[key].onerror = () => {
    // If any image failed to load, we still try to init when other images load.
    // This avoids blocking the animation if one optional part is missing.
    loaded++;
    if (loaded === totalParts) init();
  };
}

// --- Puppet definition (for ~100x100 head, 120x200 torso, 40x150 limbs) ---
const puppet = {
  x: 50, y: 400,
  torso: { angle: .15, offsetX: 0, offsetY: 15 },
  head: { angle: -.2, offsetX: 30, offsetY: -150 },
  upperArmL: { angle: .5, offsetX: 30, offsetY: -80 },
  upperArmR: { angle: -.5, offsetX: 30, offsetY: -90 },
  //
  lowerArmL: { angle: .5, offsetX: 0, offsetY: 0 },
  lowerArmR: { angle: -.5, offsetX: 0, offsetY: 0 },
  //
  upperLegL: { angle: -.6, offsetX: 0, offsetY: 40 },
  upperLegR: { angle: .6, offsetX: 0, offsetY: 40 },
  //  
  lowerLegL: { angle: .5, offsetX: 0, offsetY: 0 },
  lowerLegR: { angle: -.5, offsetX: 0, offsetY: 0 },
  // 
  footL: { angle: 0, offsetX: 0, offsetY: 0 },
  footR: { angle: 0, offsetX: 60, offsetY: 0 }
};

// --- Initialize walking animation ---
function init() {
  const speed = 1;

  // Legs swing opposite each other
  gsap.to(puppet.upperLegL, {angle: Math.PI/6, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.lowerLegL, {angle: -Math.PI/8, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.footL,      {angle:  Math.PI/12, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});

  gsap.to(puppet.upperLegR, {angle: -Math.PI/6, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.lowerLegR, {angle:  Math.PI/8, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.footR,      {angle: -Math.PI/12, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});

  // Arms swing opposite to legs
  gsap.to(puppet.upperArmL, {angle: -Math.PI/6, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.lowerArmL, {angle: -Math.PI/12, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});

  gsap.to(puppet.upperArmR, {angle: Math.PI/6, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.lowerArmR, {angle: Math.PI/12, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});

  // Puppet forward movement loop
  gsap.to(puppet, {
    x: canvas.width, 
    duration: 60, 
    repeat: -1, 
    ease: 'linear', 
    onRepeat: () => { puppet.x = 0; }
  });

  draw();
}

// --- Draw function ---
function draw() {
  // Draw background first
  if (bgLoaded) {
    ctx.drawImage(bg, 0, 0, canvas.width, canvas.height);
  } else {
    ctx.fillStyle = "#222";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  // Draw left side limbs first for depth
  drawLimb(puppet.upperArmL, puppet.lowerArmL, parts.upperArmL, parts.lowerArmL);
  drawLimb(puppet.upperLegL, puppet.lowerLegL, parts.upperLegL, parts.lowerLegL, parts.footL);

  // Torso and head
  drawPart(parts.torso, puppet.x + puppet.torso.offsetX * scale, puppet.y + puppet.torso.offsetY * scale, puppet.torso.angle);
  drawPart(parts.head,   puppet.x + puppet.head.offsetX * scale,   puppet.y + puppet.head.offsetY * scale,   puppet.head.angle);

  drawLimb(puppet.upperLegR, puppet.lowerLegR, parts.upperLegR, parts.lowerLegR, parts.footR);

  // Right side limbs
  drawLimb(puppet.upperArmR, puppet.lowerArmR, parts.upperArmR, parts.lowerArmR);

  requestAnimationFrame(draw);
}

// --- Helper functions ---
function drawLimb(upper, lower, upperImg, lowerImg, footImg) {
  const startX = puppet.x + upper.offsetX * scale;
  const startY = puppet.y + upper.offsetY * scale;

  ctx.save();
  ctx.translate(startX, startY);
  ctx.rotate(upper.angle);
  if (upperImg && upperImg.complete) {
    ctx.drawImage(upperImg, -upperImg.width/2 * scale, 0, upperImg.width * scale, upperImg.height * scale);
  }

  // Slightly shorten joint connection to bring limbs closer
  ctx.translate(0, (upperImg && upperImg.height ? upperImg.height : 100) * scale * 0.9);
  ctx.rotate(lower.angle);
  if (lowerImg && lowerImg.complete) {
    ctx.drawImage(lowerImg, -lowerImg.width/2 * scale, 0, lowerImg.width * scale, lowerImg.height * scale);
  }

  if (footImg) {
    ctx.translate(0, (lowerImg && lowerImg.height ? lowerImg.height : 100) * scale * 0.9);
    ctx.rotate(footImg.angle || 0);
    if (footImg.complete) {
      ctx.drawImage(footImg, -footImg.width/2 * scale, 0, footImg.width * scale, footImg.height * scale);
    }
  }

  ctx.restore();
}

function drawPart(img, x, y, angle=0) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  if (img && img.complete) {
    ctx.drawImage(img, -img.width/2 * scale, -img.height/2 * scale, img.width * scale, img.height * scale);
  }
  ctx.restore();
}
</script>
</body>
</html>
"""

# -----------------------------
# Routes
# -----------------------------

@app.route("/")
def index():
    ic("Serving index")
    return render_template_string(INDEX_HTML, PART_FILES=PART_FILES)

@app.route("/upload/<part_name>", methods=["POST"])
def upload_part(part_name):
    if part_name not in PART_FILES:
        ic("Invalid upload part requested:", part_name)
        return "Invalid part", 400

    file = request.files.get("file")
    if not file:
        ic("No file provided for", part_name)
        return "No file", 400

    filename = PART_FILES[part_name]
    save_path = os.path.join(STATIC_DIR, filename)

    try:
        file.save(save_path)
        ic("Saved:", save_path)
    except Exception as e:
        ic("Failed to save:", save_path, "error:", e)
        return "Save failed", 500

    # Redirect back to index so you can see preview
    return redirect(url_for("index"))

@app.route("/animation")
def animation():
    ic("Serving animation page")
    return render_template_string(ANIMATION_HTML)

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    ic("Starting app on http://0.0.0.0:5200")
    app.run(host="0.0.0.0", port=5200, debug=True)
