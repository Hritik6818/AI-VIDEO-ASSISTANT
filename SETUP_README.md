# AI Meeting Assistant — Setup Guide

Two parts: the **FastAPI backend** (wraps your existing pipeline) and the
**React frontend** (Vite). Run both at once, in two terminals.

---

## 1. Project layout

Place the new files into your existing project like this:

```
C:\GEN-AI\AI-ASSISTANT-PROECT\
├── api\
│   └── main.py              <-- new (FastAPI backend)
├── core\
│   ├── transcriber.py        (already have)
│   ├── sammarize.py          (already have)
│   ├── extractor.py          (already have)
│   └── Rag_Engine.py         (already have)
├── utils\
│   └── audio_processor.py    (already have)
├── frontend\                <-- new (React app, entire folder)
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── src\
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       └── components\
│           ├── Loader.jsx
│           ├── ResultView.jsx
│           └── ChatPanel.jsx
├── main.py                   (your existing CLI entry point — untouched)
├── Requirements.txt
└── .env
```

`api/main.py` imports from `utils.` and `core.` exactly like your existing
`main.py` does, so it must live in an `api/` folder **at the project root**,
not inside `utils/` or `core/`.

---

## 2. Backend setup

Your `Requirements.txt` already has `fastapi`, `uvicorn[standard]`, and
`python-multipart` from earlier in this project — nothing new to install.

Create an `api/__init__.py` (can be empty) so Python treats `api/` as a package:

```powershell
New-Item -ItemType File -Path "api\__init__.py"
```

Also make sure `core/__init__.py` and `utils/__init__.py` exist (empty files
are fine) if you don't already have them — needed for the imports to resolve.

**Run the backend** from the project root:

```powershell
cd C:\GEN-AI\AI-ASSISTANT-PROECT
uvicorn api.main:app --reload --port 8000
```

Verify it's up: open http://localhost:8000/api/health — should return
`{"status":"ok"}`.

---

## 3. Frontend setup

Requires [Node.js](https://nodejs.org/) (LTS version, 18+). Check with:

```powershell
node --version
```

Then, in a **second terminal**:

```powershell
cd C:\GEN-AI\AI-ASSISTANT-PROECT\frontend
npm install
npm run dev
```

Open the URL it prints — typically **http://localhost:5173**.

The Vite dev server proxies `/api/*` requests to `http://localhost:8000`
(configured in `vite.config.js`), so the frontend and backend talk to each
other automatically — no CORS setup needed beyond what's already in
`api/main.py`.

---

## 4. Using it

1. With both servers running, open http://localhost:5173
2. Paste a YouTube URL (or switch to "Upload File") and pick a language
3. Click **Process Meeting** — you'll see a live progress indicator
   (downloading → transcribing → summarizing → extracting → indexing)
4. Once done: browse Summary / Action Items / Key Decisions / Open Questions
   / Full Transcript in the tab rail, export as PDF or TXT, or ask questions
   in the chat panel at the bottom

---

## 5. Environment variables

No changes to your existing `.env` — same keys as before:

```env
MISTRAL_API_KEY=your_mistral_key
SARVAM_API_KEY=your_sarvam_key
SARVAM_STT_MODEL=saaras:v3
WHISPER_MODEL=small
```

---

## 6. Common issues

**Frontend loads but "Process Meeting" does nothing / network error**
→ Backend isn't running, or crashed. Check the `uvicorn` terminal for errors.

**CORS error in browser console**
→ Confirm you're opening the frontend at `http://localhost:5173` exactly
(not `127.0.0.1:5173`) — `api/main.py`'s CORS config allows both, but
double-check if you changed ports.

**Job stays stuck on one status forever**
→ Check the `uvicorn` terminal — the actual Python traceback from your
pipeline (transcriber/summarizer/etc.) prints there, since the frontend
only shows a generic error.

**"Module not found: api"**
→ Make sure `api/__init__.py` exists and you're running `uvicorn` from the
project root (`C:\GEN-AI\AI-ASSISTANT-PROECT`), not from inside `api/`.

---

## 7. Building for production later (optional, not needed for local use)

```powershell
cd frontend
npm run build
```

This outputs static files to `frontend/dist/` — you could later serve these
directly from FastAPI with `StaticFiles`, or deploy separately (e.g. Vercel
for frontend, a VPS for backend). Not required for local/dev use — `npm run
dev` is fine for that.

# 🎥 AI Video Assistant

An AI-powered video assistant that downloads audio from YouTube,
transcribes it using Faster-Whisper, generates a title and creates
an AI-powered summary using Mistral AI.

## 🚀 Features

- YouTube video input
- Audio extraction
- Audio chunking
- Faster-Whisper transcription
- English / Hindi / Hinglish support
- AI-generated title
- AI-generated summary
- Mistral AI integration

## 🏗️ Architecture

YouTube URL
↓
Audio Downloader
↓
Audio Chunking
↓
Faster-Whisper
↓
Transcript
↓
Mistral AI
↓
Title + Summary

## 🛠️ Technologies

- Python
- Faster-Whisper
- LangChain
- Mistral AI
- YouTube
- Python-dotenv

## ⚙️ Installation

Clone the repository:

git clone https://github.com/YOUR_USERNAME/ai-video-assistant.git

cd ai-video-assistant

Create virtual environment:

python -m venv .venv

Activate:

.venv\Scripts\activate

Install dependencies:

pip install -r Requirements.txt

Create `.env`:

MISTRAL_API_KEY=your_api_key_here

Run:

python test.py
