#!/usr/bin/env python3
"""
GSAP / GASP Studio - Base Flask app (complete)

Features:
- Persistent upload endpoint (keeps upload functionality intact)
  - upload types: 'upload' (general), 'background', 'overlay'
- Text editor CRUD (create/read/update/delete/download) stored under ./static/text/
- SQLite3 schema for projects/assets/frames/frame_layers/documents/videos
- ChromaDB initialization and text indexing (on text save/update)
- Hard-copy debug logging using icecream.ic (writes to ./logs/debug_YYYY-MM-DD.txt)
- Asset dimension detection using Pillow
- Safely handles filenames using secure_filename
- No use of logging module (uses icecream per your preference)
- Does not remove or hide any existing functionality
"""

import os
import sqlite3
import datetime
import uuid
import json
from pathlib import Path
from flask import (
    Flask, request, render_template, redirect,
    url_for, send_from_directory, flash, jsonify
)
from icecream import ic
import chromadb
from chromadb.utils import embedding_functions
from werkzeug.utils import secure_filename
from PIL import Image

# ===========================
# CONFIGURATION
# ===========================
APP_PORT = 5300
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")       # general uploads (kept)
BACKGROUNDS_DIR = os.path.join(STATIC_DIR, "backgrounds")
OVERLAYS_DIR = os.path.join(STATIC_DIR, "overlays")
TEXT_DIR = os.path.join(STATIC_DIR, "text")
OUTPUTS_DIR = os.path.join(STATIC_DIR, "outputs")

DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "animation.db")
CHROMA_DIR = os.path.join(DB_DIR, "chroma")

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_OVERLAY_EXTENSIONS = {".png"}  # overlays should be PNG (alpha)

# Ensure required directories exist
for d in [
    STATIC_DIR, UPLOADS_DIR, BACKGROUNDS_DIR, OVERLAYS_DIR,
    TEXT_DIR, OUTPUTS_DIR, DB_DIR, CHROMA_DIR
]:
    os.makedirs(d, exist_ok=True)

# ===========================
# HARD-COPY DEBUGGING (icecream)
# ===========================
log_file_path = os.path.join(LOG_DIR, f"debug_{datetime.date.today().isoformat()}.txt")

def _write_log_and_print(*args):
    """
    Write log to file and print to stdout. This is used as icecream's outputFunction.
    """
    try:
        s = " ".join(map(str, args))
        # Prepend timestamp for clarity in hard-copy logs
        timestamp = datetime.datetime.now().isoformat()
        line = f"{timestamp} | {s}\n"
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        # Avoid raising inside logging function
        print("Failed to write log:", e)
    # still print to console / terminal
    print(*args)

# Configure icecream to use our writer
ic.configureOutput(prefix="ic| ", outputFunction=_write_log_and_print, includeContext=True)
ic("Starting GASP/GSAP Studio Flask app (app.py)")

# ===========================
# FLASK APP
# ===========================
app = Flask(__name__)
# secret key for flash messages; local dev only
app.secret_key = "gasp_studio_dev_secret"

# ===========================
# DATABASE (SQLite) HELPERS
# ===========================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Create all required tables if they don't exist.
    This is intentionally additive and safe to run multiple times.
    """
    conn = get_conn()
    c = conn.cursor()

    # projects
    c.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # assets: backgrounds, overlays, audio, other
    c.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        filename TEXT,
        type TEXT,
        width INTEGER,
        height INTEGER,
        uploaded_at TEXT,
        metadata TEXT
    )
    """)

    # frames (per project timeline)
    c.execute("""
    CREATE TABLE IF NOT EXISTS frames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        frame_index INTEGER,
        background_asset_id INTEGER,
        duration REAL,
        created_at TEXT
    )
    """)

    # layers per frame
    c.execute("""
    CREATE TABLE IF NOT EXISTS frame_layers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        frame_id INTEGER,
        asset_id INTEGER,
        x INTEGER,
        y INTEGER,
        z_index INTEGER,
        scale REAL,
        rotation REAL,
        opacity REAL
    )
    """)

    # document tracker
    c.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        project_id INTEGER,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # rendered videos
    c.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        filename TEXT,
        width INTEGER,
        height INTEGER,
        fps INTEGER,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()
    ic("SQLite DB initialized and tables are ready.")

init_db()

# ===========================
# ChromaDB Setup
# ===========================
ic("Initializing ChromaDB persistent client...")
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    # DefaultEmbeddingFunction is safe placeholder; replace with your local embed model if desired
    embed_fn = embedding_functions.DefaultEmbeddingFunction()
    chroma_collection = chroma_client.get_or_create_collection(
        name="animation_docs",
        embedding_function=embed_fn
    )
    ic("ChromaDB collection ready: animation_docs")
except Exception as e:
    chroma_client = None
    chroma_collection = None
    ic("ChromaDB initialization failed or not available:", e)

# ===========================
# UTILITIES
# ===========================
def allowed_file_extension(filename, allowed_set):
    ext = os.path.splitext(filename.lower())[1]
    return ext in allowed_set

def save_asset_file(storage_file, dest_dir, filename_override=None):
    """
    Save a Werkzeug file storage object to destination directory and return saved filename.
    """
    orig_name = storage_file.filename
    safe = secure_filename(orig_name)
    if filename_override:
        safe = secure_filename(filename_override)
    save_path = os.path.join(dest_dir, safe)
    storage_file.save(save_path)
    return safe, save_path

def get_image_size(path):
    try:
        with Image.open(path) as im:
            return im.width, im.height
    except Exception as e:
        ic("Failed to get image size for", path, ":", e)
        return None, None

def index_document_to_chroma(doc_id, filename, content):
    """
    Index or update a document into ChromaDB collection.
    Uses filename-based id to make updates idempotent.
    """
    if chroma_collection is None:
        ic("Chroma collection not available; skipping indexing for", filename)
        return
    try:
        doc_uuid = f"doc::{filename}"
        metadata = {"filename": filename}
        # Try to add; if exists, update
        try:
            chroma_collection.add(
                ids=[doc_uuid],
                documents=[content],
                metadatas=[metadata]
            )
            ic("Added document to Chroma:", filename)
        except Exception:
            # fallback to update if already present
            chroma_collection.update(
                ids=[doc_uuid],
                documents=[content],
                metadatas=[metadata]
            )
            ic("Updated document in Chroma:", filename)
    except Exception as e:
        ic("Chroma indexing error for", filename, ":", e)

# ===========================
# ROUTES - Pages & API
# ===========================

@app.route("/")
def index():
    """
    Dashboard index page.
    Shows basic counts and links to features.
    """
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM assets")
    assets_count = c.fetchone()["cnt"]
    c.execute("SELECT COUNT(*) as cnt FROM documents")
    docs_count = c.fetchone()["cnt"]
    c.execute("SELECT COUNT(*) as cnt FROM projects")
    projects_count = c.fetchone()["cnt"]
    conn.close()
    return render_template("index.html",
                           assets_count=assets_count,
                           docs_count=docs_count,
                           projects_count=projects_count)

# ---------------------------
# ASSETS: upload & listing
# ---------------------------
@app.route("/assets")
def assets_list():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM assets ORDER BY uploaded_at DESC")
    rows = c.fetchall()
    conn.close()
    return render_template("assets.html", assets=rows)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    """
    Accepts form-data:
    - file: uploaded file
    - type: 'upload' (general), 'background', or 'overlay' (default 'upload')
    - project_id: optional integer
    """
    if request.method == "GET":
        # show a minimal upload helper page if visited directly
        return render_template("upload.html")

    file = request.files.get("file")
    if not file or file.filename == "":
        flash("No file selected", "error")
        ic("Upload attempted with no file.")
        return redirect(url_for("assets_list"))

    upload_type = request.form.get("type", "upload")  # 'background', 'overlay', or 'upload'
    project_id = request.form.get("project_id") or None

    # choose destination dir and allowed extensions
    if upload_type == "background":
        dest_dir = BACKGROUNDS_DIR
        allowed = ALLOWED_IMAGE_EXTENSIONS
    elif upload_type == "overlay":
        dest_dir = OVERLAYS_DIR
        allowed = ALLOWED_OVERLAY_EXTENSIONS
    else:
        dest_dir = UPLOADS_DIR
        allowed = ALLOWED_IMAGE_EXTENSIONS

    # secure name and validate extension
    orig_name = file.filename
    safe_name = secure_filename(orig_name)
    ext = os.path.splitext(safe_name.lower())[1]
    if ext == "" or ext not in allowed:
        flash(f"File extension not allowed for type '{upload_type}': {ext}", "error")
        ic("Rejected upload (bad extension)", orig_name, "as type", upload_type)
        return redirect(url_for("assets_list"))

    # save the file
    saved_name, saved_path = save_asset_file(file, dest_dir)
    width, height = get_image_size(saved_path)
    now = datetime.datetime.now().isoformat()

    # write to DB
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO assets (project_id, filename, type, width, height, uploaded_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (project_id, saved_name, upload_type, width, height, now, json.dumps({}))
    )
    conn.commit()
    conn.close()

    ic("Uploaded asset:", saved_name, "type:", upload_type, "size:", f"{width}x{height}")
    flash(f"Uploaded {saved_name} as {upload_type}", "success")
    return redirect(url_for("assets_list"))

@app.route("/assets/delete/<int:asset_id>")
def assets_delete(asset_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT filename, type FROM assets WHERE id=?", (asset_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        flash("Asset not found", "error")
        ic("Attempted delete of non-existent asset id:", asset_id)
        return redirect(url_for("assets_list"))

    filename = row["filename"]
    atype = row["type"]
    # determine file path
    if atype == "background":
        path = os.path.join(BACKGROUNDS_DIR, filename)
    elif atype == "overlay":
        path = os.path.join(OVERLAYS_DIR, filename)
    else:
        path = os.path.join(UPLOADS_DIR, filename)

    # delete file safely
    try:
        if os.path.exists(path):
            os.remove(path)
            ic("Deleted asset file:", path)
    except Exception as e:
        ic("Failed to remove file:", path, e)

    c.execute("DELETE FROM assets WHERE id=?", (asset_id,))
    conn.commit()
    conn.close()
    flash(f"Deleted asset {filename}", "info")
    return redirect(url_for("assets_list"))

# Serve uploaded static files from their directories
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOADS_DIR, filename)

@app.route("/backgrounds/<path:filename>")
def background_file(filename):
    return send_from_directory(BACKGROUNDS_DIR, filename)

@app.route("/overlays/<path:filename>")
def overlay_file(filename):
    return send_from_directory(OVERLAYS_DIR, filename)

# ---------------------------
# TEXT DOCUMENT CRUD
# ---------------------------
@app.route("/text")
def text_index():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, filename, created_at, updated_at FROM documents ORDER BY updated_at DESC")
    docs = c.fetchall()
    conn.close()
    return render_template("text_index.html", docs=docs)

@app.route("/text/new", methods=["GET", "POST"])
def text_new():
    if request.method == "POST":
        filename_in = request.form.get("filename", "").strip()
        content = request.form.get("content", "")
        if filename_in == "":
            flash("Filename is required", "error")
            return redirect(url_for("text_new"))
        #if not filename_in.endswith(".txt"):
        #    filename_in = filename_in + ".txt"
        filename_safe = secure_filename(filename_in)
        save_path = os.path.join(TEXT_DIR, filename_safe)

        # write file
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(content)

        now = datetime.datetime.now().isoformat()
        conn = get_conn()
        c = conn.cursor()
        # insert or replace metadata record
        c.execute(
            "INSERT OR REPLACE INTO documents (filename, created_at, updated_at) VALUES (?, COALESCE((SELECT created_at FROM documents WHERE filename=?), ?), ?)",
            (filename_safe, filename_safe, now, now)
        )
        conn.commit()
        conn.close()

        ic("Created new text document:", filename_safe, "chars:", len(content))

        # index into ChromaDB (non-blocking best attempted; here synchronous)
        try:
            index_document_to_chroma(None, filename_safe, content)
        except Exception as e:
            ic("Chroma indexing skipped/failed for", filename_safe, e)

        flash(f"Saved {filename_safe}", "success")
        return redirect(url_for("text_index"))

    # GET: show new doc form
    return render_template("text_edit.html", mode="new", filename="", content="")

@app.route("/text/edit/<path:filename>", methods=["GET", "POST"])
def text_edit(filename):
    filename_safe = secure_filename(filename)
    file_path = os.path.join(TEXT_DIR, filename_safe)

    if request.method == "POST":
        content = request.form.get("content", "")
        # ensure parent exists
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        now = datetime.datetime.now().isoformat()
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE documents SET updated_at=? WHERE filename=?", (now, filename_safe))
        conn.commit()
        conn.close()

        ic("Saved text document:", filename_safe, "size:", len(content))

        # Chroma index update
        try:
            index_document_to_chroma(None, filename_safe, content)
        except Exception as e:
            ic("Chroma update failed for", filename_safe, e)

        flash(f"Saved {filename_safe}", "success")
        return redirect(url_for("text_index"))

    # GET: load existing content
    content = ""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

    return render_template("text_edit.html", mode="edit", filename=filename_safe, content=content)

@app.route("/text/delete/<path:filename>")
def text_delete(filename):
    filename_safe = secure_filename(filename)
    path = os.path.join(TEXT_DIR, filename_safe)
    if os.path.exists(path):
        os.remove(path)
        ic("Deleted text file:", filename_safe)
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM documents WHERE filename=?", (filename_safe,))
    conn.commit()
    conn.close()

    # remove from Chroma if possible
    if chroma_collection:
        try:
            chroma_collection.delete(ids=[f"doc::{filename_safe}"])
            ic("Deleted document from Chroma:", filename_safe)
        except Exception as e:
            ic("Chroma delete failed (maybe not indexed):", e)

    flash(f"Deleted {filename_safe}", "info")
    return redirect(url_for("text_index"))

@app.route("/text/download/<path:filename>")
def text_download(filename):
    filename_safe = secure_filename(filename)
    return send_from_directory(TEXT_DIR, filename_safe, as_attachment=True)

# ---------------------------
# PROJECTS / TIMELINE (skeleton endpoints)
# ---------------------------
@app.route("/projects")
def projects_list():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM projects ORDER BY updated_at DESC")
    rows = c.fetchall()
    conn.close()
    return render_template("projects.html", projects=rows)

@app.route("/projects/new", methods=["POST"])
def projects_new():
    name = request.form.get("name", "untitled").strip()
    description = request.form.get("description", "")
    now = datetime.datetime.now().isoformat()
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO projects (name, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
              (name, description, now, now))
    conn.commit()
    conn.close()
    ic("Created project:", name)
    return redirect(url_for("projects_list"))

# timeline view (skeleton)
@app.route("/timeline/<int:project_id>")
def timeline(project_id):
    conn = get_conn()
    c = conn.cursor()
    # frames for this project
    c.execute("SELECT * FROM frames WHERE project_id=? ORDER BY frame_index ASC", (project_id,))
    frames = c.fetchall()
    # list project assets for possible assignment
    c.execute("SELECT * FROM assets WHERE project_id=? OR project_id IS NULL", (project_id,))
    assets = c.fetchall()
    conn.close()
    return render_template("timeline.html", project_id=project_id, frames=frames, assets=assets)

@app.route("/export/video/<int:project_id>", methods=["POST"])
def export_video(project_id):
    """
    Placeholder export function: reads frames and logs the ffmpeg command that would be executed.
    This function intentionally logs detailed steps into the hard-copy log so you can inspect.
    """
    ic("Export requested for project:", project_id)
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM frames WHERE project_id=? ORDER BY frame_index ASC", (project_id,))
    frames = c.fetchall()
    conn.close()

    # For now we do a dry-run: log what we'd do and return success
    ic("Frames to render:", len(frames))
    out_dir = os.path.join(OUTPUTS_DIR, f"project_{project_id}")
    os.makedirs(out_dir, exist_ok=True)
    ic("Output frames would be written to:", out_dir)

    # Example ffmpeg command that we would run after composing frames:
    ffmpeg_cmd = (
        f"ffmpeg -framerate 30 -i {os.path.join(out_dir, 'frame_%05d.png')} "
        f"-c:v libx264 -pix_fmt yuv420p {os.path.join(out_dir, f'project_{project_id}.mp4')}"
    )
    ic("FFMPEG (dry-run) command:", ffmpeg_cmd)

    # Return JSON so UI can show result
    return jsonify({"status": "ok", "frames": len(frames), "ffmpeg_cmd": ffmpeg_cmd})

# ---------------------------
# LOGS viewer (read-only)
# ---------------------------
@app.route("/logs/latest")
def logs_latest():
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""
    return render_template("logs.html", content=content)

# ===========================
# RUN
# ===========================
if __name__ == "__main__":
    ic(f"App starting on http://localhost:{APP_PORT}")
    # debug=True for development only
    app.run(host="0.0.0.0", port=APP_PORT, debug=True)
