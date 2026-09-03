"""
FastAPI backend for the AI Meeting Assistant.

Wraps the existing pipeline (audio_processor -> transcriber -> summarizer ->
extractor -> Rag_Engine) behind REST endpoints so the React frontend can:
  - submit a YouTube URL or uploaded file for processing
  - poll job status while it runs in the background
  - fetch the final result (title, summary, action items, decisions, questions)
  - chat with the transcript via the RAG chain
  - export the result as PDF or TXT

Run from the project root:
    uvicorn api.main:app --reload --port 8000
"""

import os
import io
import uuid
import shutil
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.sammarize import summarize, generate_title
from core.extractor import extract_action_item, extract_key_decisions, extract_questions
from core.Rag_Engine import build_rag_chain, ask_question

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="AI Meeting Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Single background worker: transcription/LLM calls are CPU/network bound
# and this project runs as a single-user local tool, so one worker keeps
# resource usage predictable rather than spawning unbounded threads.
executor = ThreadPoolExecutor(max_workers=1)

# In-memory job store. Fine for a local/dev single-process server;
# swap for Redis or a DB if this ever needs to run multi-process.
JOBS: dict = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ProcessRequest(BaseModel):
    source: str
    language: str = "english"  # "english" | "hindi" | "hinglish"


class ChatRequest(BaseModel):
    question: str


# ---------------------------------------------------------------------------
# Pipeline runner (executed in the background thread)
# ---------------------------------------------------------------------------

def _run_pipeline(job_id: str, source: str, language: str):
    try:
        JOBS[job_id]["status"] = "downloading"
        chunks = process_input(source)

        JOBS[job_id]["status"] = "transcribing"
        transcript = transcribe_all(chunks, language)

        JOBS[job_id]["status"] = "summarizing"
        title = generate_title(transcript)
        summary = summarize(transcript)

        JOBS[job_id]["status"] = "extracting"
        action_items = extract_action_item(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)

        JOBS[job_id]["status"] = "indexing"
        rag_chain = build_rag_chain(transcript)

        JOBS[job_id].update({
            "status": "done",
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items,
            "key_decisions": decisions,
            "open_questions": questions,
            "rag_chain": rag_chain,
            "error": None,
        })
    except Exception as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Save an uploaded audio/video file and return its server-side path,
    to be passed as `source` to /api/process."""
    dest_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{file.filename}")
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"path": dest_path, "filename": file.filename}


@app.post("/api/process")
def start_processing(payload: ProcessRequest):
    """Kick off the pipeline in the background. Returns immediately with a job_id."""
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "queued", "error": None}
    executor.submit(_run_pipeline, job_id, payload.source, payload.language)
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
def get_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": job["status"], "error": job.get("error")}


@app.get("/api/result/{job_id}")
def get_result(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail=f"Job not finished (status: {job['status']})")

    return {
        "title": job["title"],
        "transcript": job["transcript"],
        "summary": job["summary"],
        "action_items": job["action_items"],
        "key_decisions": job["key_decisions"],
        "open_questions": job["open_questions"],
    }


@app.post("/api/chat/{job_id}")
def chat(job_id: str, payload: ChatRequest):
    job = JOBS.get(job_id)
    if not job or job.get("status") != "done":
        raise HTTPException(status_code=409, detail="Meeting not ready for chat yet")

    answer = ask_question(job["rag_chain"], payload.question)
    return {"answer": answer}


@app.get("/api/export/{job_id}/txt")
def export_txt(job_id: str):
    job = JOBS.get(job_id)
    if not job or job.get("status") != "done":
        raise HTTPException(status_code=409, detail="Meeting not ready yet")

    content = (
        f"{job['title']}\n"
        f"{'=' * len(job['title'])}\n\n"
        f"SUMMARY\n-------\n{job['summary']}\n\n"
        f"ACTION ITEMS\n------------\n{job['action_items']}\n\n"
        f"KEY DECISIONS\n-------------\n{job['key_decisions']}\n\n"
        f"OPEN QUESTIONS\n--------------\n{job['open_questions']}\n\n"
        f"FULL TRANSCRIPT\n---------------\n{job['transcript']}\n"
    )
    buf = io.BytesIO(content.encode("utf-8"))
    return StreamingResponse(
        buf,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{job["title"][:50]}.txt"'},
    )


@app.get("/api/export/{job_id}/pdf")
def export_pdf(job_id: str):
    job = JOBS.get(job_id)
    if not job or job.get("status") != "done":
        raise HTTPException(status_code=409, detail="Meeting not ready yet")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=colors.HexColor("#1C1F27"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#E8A33D"))
    body = ParagraphStyle("Body", parent=styles["BodyText"], leading=16)

    def section(title, text):
        return [Paragraph(title, h2), Paragraph(str(text).replace("\n", "<br/>"), body), Spacer(1, 12)]

    story = [Paragraph(job["title"], h1), Spacer(1, 16)]
    story += section("Summary", job["summary"])
    story += section("Action Items", job["action_items"])
    story += section("Key Decisions", job["key_decisions"])
    story += section("Open Questions", job["open_questions"])
    story += section("Full Transcript", job["transcript"])

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{job["title"][:50]}.pdf"'},
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}
