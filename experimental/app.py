#!/usr/bin/env python3
from flask import Flask, request, send_from_directory, render_template_string, redirect
import os
from icecream import ic

app = Flask(__name__)

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
STATIC_DIR = os.path.join(os.getcwd(), "static")

VALID_IMAGES = [
    "torso.png",
    "head.png",
    "uarml.png",
    "larml.png",
    "uarmr.png",
    "larmr.png",
    "ulegl.png",
    "llegl.png",
    "ulegr.png",
    "llegr.png",
    "footl.png",
    "footr.png",
    "back512.jpg"
]

# -------------------------------------------------------------------
# HTML: HOMEPAGE
# -------------------------------------------------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Puppet Menu</title>
<style>
body {
    background: #111;
    color: #eee;
    font-family: Arial;
    padding: 40px;
}
.container {
    max-width: 500px;
    margin: auto;
    background: #222;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
}
a {
    display: block;
    background: #444;
    color: #fff;
    padding: 12px;
    margin: 10px 0;
    border-radius: 6px;
    text-decoration: none;
}
a:hover {
    background: #666;
}
</style>
</head>
<body>
<div class="container">
    <h2>Puppet System</h2>
    <a href="/upload">Upload Puppet Images</a>
    <a href="/animation">View Animation</a>
</div>
</body>
</html>
"""

# -------------------------------------------------------------------
# HTML: UPLOAD PAGE
# -------------------------------------------------------------------
UPLOAD_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Upload Puppet Parts</title>
<style>
body {
    background: #181818;
    color: #eee;
    font-family: Arial, sans-serif;
    padding: 20px;
}
.container {
    max-width: 500px;
    margin: auto;
    padding: 20px;
    background: #222;
    border-radius: 10px;
}
input[type=file] {
    width: 100%;
}
button {
    margin-top: 15px;
    padding: 10px 20px;
    border: none;
    background: #28a745;
    color: white;
    cursor: pointer;
    border-radius: 5px;
}
button:hover {
    background: #218838;
}
a {
    display: inline-block;
    margin-top: 20px;
    color: #57a6ff;
}
</style>
</head>
<body>

<div class="container">
    <h2>Upload Puppet Image Parts</h2>
    <p>Upload one or many images at once. Only files with known puppet names will replace existing parts.</p>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="images" multiple>
        <button type="submit">Upload Files</button>
    </form>

    <a href="/">Back to Menu</a>
    <a href="/animation">View Animation</a>
</div>
</body>
</html>
"""

# -------------------------------------------------------------------
# HTML: ANIMATION PAGE
# -------------------------------------------------------------------
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
bg.src = "/static/back512.jpg";
let bgLoaded = false;
bg.onload = () => bgLoaded = true;

// --- Load images ---
const parts = {};

const partFiles = {
  torso: "/static/torso.png",
  head: "/static/head.png",
  upperArmL: "/static/uarml.png",
  lowerArmL: "/static/larml.png",
  upperArmR: "/static/uarmr.png",
  lowerArmR: "/static/larmr.png",
  upperLegL: "/static/ulegl.png",
  lowerLegL: "/static/llegl.png",
  upperLegR: "/static/ulegr.png",
  lowerLegR: "/static/llegr.png",
  footL: "/static/footl.png",
  footR: "/static/footr.png"
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
}

// --- Puppet definition ---
const puppet = {
  x: 50, y: 400,
  torso: { angle: .15, offsetX: 0, offsetY: 15 },
  head: { angle: -.2, offsetX: 30, offsetY: -150 },
  upperArmL: { angle: .5, offsetX: 30, offsetY: -80 },
  upperArmR: { angle: -.5, offsetX: 30, offsetY: -90 },
  lowerArmL: { angle: .5, offsetX: 0, offsetY: 0 },
  lowerArmR: { angle: -.5, offsetX: 0, offsetY: 0 },
  upperLegL: { angle: -.6, offsetX: 0, offsetY: 40 },
  upperLegR: { angle: .6, offsetX: 0, offsetY: 40 },
  lowerLegL: { angle: .5, offsetX: 0, offsetY: 0 },
  lowerLegR: { angle: -.5, offsetX: 0, offsetY: 0 },
  footL: { angle: 0, offsetX: 0, offsetY: 0 },
  footR: { angle: 0, offsetX: 60, offsetY: 0 }
};

function init() {
  const speed = 1;

  gsap.to(puppet.upperLegL, {angle: Math.PI/6, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.lowerLegL, {angle: -Math.PI/8, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.footL,      {angle:  Math.PI/12, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});

  gsap.to(puppet.upperLegR, {angle: -Math.PI/6, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.lowerLegR, {angle: Math.PI/8, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.footR,      {angle: -Math.PI/12, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});

  gsap.to(puppet.upperArmL, {angle: -Math.PI/6, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.lowerArmL, {angle: -Math.PI/12, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});

  gsap.to(puppet.upperArmR, {angle: Math.PI/6, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});
  gsap.to(puppet.lowerArmR, {angle: Math.PI/12, duration:speed, yoyo:true, repeat:-1, ease:'sine.inOut'});

  gsap.to(puppet, {
    x: canvas.width, 
    duration: 60, 
    repeat: -1, 
    ease: 'linear', 
    onRepeat: () => { puppet.x = 0; }
  });

  draw();
}

function draw() {
  if (bgLoaded) {
    ctx.drawImage(bg, 0, 0, canvas.width, canvas.height);
  } else {
    ctx.fillStyle = "#222";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  drawLimb(puppet.upperArmL, puppet.lowerArmL, parts.upperArmL, parts.lowerArmL);
  drawLimb(puppet.upperLegL, puppet.lowerLegL, parts.upperLegL, parts.lowerLegL, parts.footL);

  drawPart(parts.torso, puppet.x + puppet.torso.offsetX * scale, puppet.y + puppet.torso.offsetY * scale, puppet.torso.angle);
  drawPart(parts.head,   puppet.x + puppet.head.offsetX * scale,   puppet.y + puppet.head.offsetY * scale,   puppet.head.angle);

  drawLimb(puppet.upperLegR, puppet.lowerLegR, parts.upperLegR, parts.lowerLegR, parts.footR);
  drawLimb(puppet.upperArmR, puppet.lowerArmR, parts.upperArmR, parts.lowerArmR);

  requestAnimationFrame(draw);
}

function drawLimb(upper, lower, upperImg, lowerImg, footImg) {
  const startX = puppet.x + upper.offsetX * scale;
  const startY = puppet.y + upper.offsetY * scale;

  ctx.save();
  ctx.translate(startX, startY);
  ctx.rotate(upper.angle);
  ctx.drawImage(upperImg, -upperImg.width/2 * scale, 0, upperImg.width * scale, upperImg.height * scale);

  ctx.translate(0, upperImg.height * scale * 0.9);
  ctx.rotate(lower.angle);
  ctx.drawImage(lowerImg, -lowerImg.width/2 * scale, 0, lowerImg.width * scale, lowerImg.height * scale);

  if (footImg) {
    ctx.translate(0, lowerImg.height * scale * 0.9);
    ctx.rotate(footImg.angle || 0);
    ctx.drawImage(footImg, -footImg.width/2 * scale, 0, footImg.width * scale, footImg.height * scale);
  }

  ctx.restore();
}

function drawPart(img, x, y, angle=0) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  ctx.drawImage(img, -img.width/2 * scale, -img.height/2 * scale, img.width * scale, img.height * scale);
  ctx.restore();
}
</script>
</body>
</html>
"""

# -------------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------------

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/animation")
def animation():
    return render_template_string(ANIMATION_HTML)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        files = request.files.getlist("images")
        for file in files:
            filename = file.filename.lower().strip()
            ic("Uploaded:", filename)

            if filename in VALID_IMAGES:
                save_path = os.path.join(STATIC_DIR, filename)
                file.save(save_path)
                ic("Saved to:", save_path)
            else:
                ic("Ignored (not a puppet part):", filename)

        return redirect("/upload")

    return render_template_string(UPLOAD_HTML)

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

if __name__ == "__main__":
    if not os.path.exists(STATIC_DIR):
        os.makedirs(STATIC_DIR)
    app.run(host="0.0.0.0", port=5050, debug=True)
