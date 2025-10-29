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
TEXT_FOLDER = "./static/text"
DB_PATH = "./db/animation.db"
LOG_FOLDER = "./logs"
CHROMA_PATH = "./db/chroma"
COLLECTION_NAME = "animation_docs"

# Ensure folders exist
for folder in [UPLOAD_FOLDER, TEXT_FOLDER, LOG_FOLDER, "./db"]:
    os.makedirs(folder, exist_ok=True)

# ----------------------------------------------------------
# Hard Copy Debug Setup
# ----------------------------------------------------------
log_file = os.path.join(LOG_FOLDER, f"debug_{datetime.date.today()}.txt")
ic.configureOutput(prefix='[DEBUG] | ', outputFunction=lambda *a: print(*a) or open(log_file, "a").write(" ".join(map(str, a)) + "\n"))

ic("Starting GSAP Studio Base App with Text Editor")

# ----------------------------------------------------------
# Flask Setup
# ----------------------------------------------------------
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["TEXT_FOLDER"] = TEXT_FOLDER

# ----------------------------------------------------------
# SQLite3 Setup
# ----------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Frames table (for images)
    c.execute("""
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            caption TEXT,
            created_at TEXT
        )
    """)
    # Text documents table
    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            created_at TEXT,
            updated_at TEXT
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

# ==========================================================
# ROUTES
# ==========================================================

@app.route("/")
def index():
    return render_template("index.html")

# ----------------------------------------------------------
# TEXT DOCUMENT ROUTES
# ----------------------------------------------------------

@app.route("/text")
def text_index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, filename, created_at, updated_at FROM documents ORDER BY updated_at DESC")
    docs = c.fetchall()
    conn.close()
    return render_template("text_index.html", docs=docs)

@app.route("/text/new", methods=["GET", "POST"])
def text_new():
    if request.method == "POST":
        filename = request.form["filename"].strip()
        content = request.form["content"]
        if not filename.endswith(".txt"):
            filename += ".txt"
        save_path = os.path.join(TEXT_FOLDER, filename)
        with open(save_path, "w") as f:
            f.write(content)
        now = datetime.datetime.now().isoformat()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO documents (filename, created_at, updated_at) VALUES (?, ?, ?)", (filename, now, now))
        conn.commit()
        conn.close()
        ic(f"New text file created: {filename}")
        return redirect(url_for("text_index"))
    return render_template("text_edit.html", mode="new", filename="", content="")

@app.route("/text/edit/<filename>", methods=["GET", "POST"])
def text_edit(filename):
    filepath = os.path.join(TEXT_FOLDER, filename)
    if request.method == "POST":
        content = request.form["content"]
        with open(filepath, "w") as f:
            f.write(content)
        now = datetime.datetime.now().isoformat()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE documents SET updated_at=? WHERE filename=?", (now, filename))
        conn.commit()
        conn.close()
        ic(f"Text file saved: {filename}")
        return redirect(url_for("text_index"))

    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            content = f.read()
    else:
        content = ""
    return render_template("text_edit.html", mode="edit", filename=filename, content=content)

@app.route("/text/delete/<filename>")
def text_delete(filename):
    filepath = os.path.join(TEXT_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        ic(f"Deleted text file: {filename}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM documents WHERE filename=?", (filename,))
    conn.commit()
    conn.close()
    return redirect(url_for("text_index"))

@app.route("/text/download/<filename>")
def text_download(filename):
    return send_from_directory(TEXT_FOLDER, filename, as_attachment=True)

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
