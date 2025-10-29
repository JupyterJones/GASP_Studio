# 🎬 GSAP Studio

**GSAP Studio** is a Flask-based creative environment for experimenting with **GreenSock (GSAP)** animations, managing image assets, creating timelines, and documenting your progress using a built-in text editor.  
It’s designed to help you build animation prototypes or stop-motion-style videos using layered assets and precise timeline control.

---

## 🚀 Features

- 🧩 **Asset Manager** — Upload, view, and organize background and overlay images  
- ✏️ **Text Editor** — Create, edit, and version your creative notes or project documentation  
- 📂 **Project System** — Manage multiple animation projects, each with its own timeline  
- 🎞️ **Timeline Editor** — Add, remove, or reposition frames, set durations and coordinates  
- 🧾 **Debug Logs Viewer** — View saved debug logs directly from the web interface  
- 🧠 **ChromaDB Integration (Optional)** — Store semantic relationships and project documentation  
- 🪶 **SQLite3 Database** — Persistent local storage for projects and assets  
- 🌗 **Dark Theme Interface** — Designed for comfort during long creative sessions  

---

## 🏗️ Directory Structure

```
GASP_Studio/
├── app.py
├── db/
│   ├── animation.db
│   └── chroma/
│       └── chroma.sqlite3
├── logs/
│   └── debug_YYYY-MM-DD.txt
├── static/
│   ├── uploads/
│   ├── backgrounds/
│   └── overlays/
├── templates/
│   ├── index.html
│   ├── assets.html
│   ├── projects.html
│   ├── timeline.html
│   ├── logs.html
│   ├── text_index.html
│   └── text_edit.html
└── text/
    └── (text documents stored here)
```

---

## ⚙️ Requirements

- Python 3.9+
- Flask
- ChromaDB
- IceCream (for debug output)

Install with:

```bash
pip install flask chromadb icecream
```

---

## ▶️ Running the App

```bash
python3 app.py
```

Then open your browser and navigate to:

```
http://127.0.0.1:5000
```

---

## 🧭 Inspection Tool

Use the included inspection script to view routes and template usage:

```bash
python3 inspect_project.py
```

This will list all Flask routes and templates and save the results to `Inspection.txt`.

---

## 💾 Logging

All debug logs are automatically written to:

```
logs/debug_YYYY-MM-DD.txt
```

You can view logs in the **Logs** tab within the web interface.

---

## 💡 Future Plans

- Add GSAP timeline preview in browser  
- Support keyframe-based animation editing  
- Integrate local AI model for scene captioning and video export  
- Add chroma semantic linking between project notes, assets, and video outputs  

---

## 🧑‍💻 Author

**Jack (JupyterJones)**  
Built with ❤️, Python, and curiosity about AI-driven creativity.  
> “The Arcanians would approve of this experiment.”

---

## 📜 License

MIT License © 2025 Jack (JupyterJones)
