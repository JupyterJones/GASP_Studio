#!/usr/bin/env python3
import os
import sqlite3
import datetime
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from icecream import ic
import chromadb
from chromadb.utils import embedding_functions

# ==========================================================
# CONFIGURATION
# ==========================================================
APP_PORT = 5300
UPLOAD_FOLDER = "./static/uploads"
DB_PATH = "./db/animation.db"
LOG_FOLDER = "./logs"
CHROMA_PATH = "./db/chroma"
COLLECTION_NAME = "animation_docs"

# Ensure folders exist
for folder in [UPLOAD_FOLDER, LOG_FOLDER, "./db"]:
    os.makedirs(folder, exist_ok=True)

# ----------------------------------------------------------
# Hard Copy Debug Setup
# ----------------------------------------------------------
log_file = os.path.join(LOG_FOLDER, f"debug_{datetime.date.today()}.txt")
ic.configureOutput(prefix='[DEBUG] | ', outputFunction=lambda *a: print(*a) or open(log_file, "a").write(" ".join(map(str, a)) + "\n"))

ic("Starting GSAP Studio Base App")

# ----------------------------------------------------------
# Flask Setup
# ----------------------------------------------------------
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ----------------------------------------------------------
# SQLite3 Setup
# ----------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            caption TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    ic("SQLite database initialized.")

init_db()

# ----------------------------------------------------------
# ChromaDB Setup
# ----------------------------------------------------------
ic("Initializing ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_PATH)
embedding_func = embedding_functions.DefaultEmbeddingFunction()
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_func
)
ic(f"ChromaDB collection ready: {COLLECTION_NAME}")

# ----------------------------------------------------------
# ROUTES
# ----------------------------------------------------------
@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, filename, caption, created_at FROM frames ORDER BY id DESC")
    frames = c.fetchall()
    conn.close()
    return render_template("index.html", frames=frames)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        ic("No file uploaded.")
        return redirect(url_for("index"))

    filename = file.filename
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    # Insert record into SQLite
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO frames (filename, caption, created_at) VALUES (?, ?, ?)",
              (filename, "No caption yet", datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

    ic(f"File uploaded: {filename}")
    return redirect(url_for("index"))

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/delete/<int:frame_id>")
def delete(frame_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT filename FROM frames WHERE id=?", (frame_id,))
    row = c.fetchone()
    if row:
        file_path = os.path.join(UPLOAD_FOLDER, row[0])
        if os.path.exists(file_path):
            os.remove(file_path)
            ic(f"Deleted file: {row[0]}")
    c.execute("DELETE FROM frames WHERE id=?", (frame_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# ==========================================================
# MAIN
# ==========================================================
if __name__ == "__main__":
    ic(f"App running on http://localhost:{APP_PORT}")
    app.run(host="0.0.0.0", port=APP_PORT, debug=True)
