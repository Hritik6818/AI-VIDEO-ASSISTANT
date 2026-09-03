import os
import glob
import requests
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
from faster_whisper import WhisperModel
from pydub import AudioSegment

_model_cache = {}

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"


# ===== Whisper (local) =====

def load_whisper_model(
    model_size: str = "base",
    device: str = "auto",
    compute_type: str = None
) -> WhisperModel:
    cache_key = (model_size, device, compute_type)
    if cache_key in _model_cache:
        return _model_cache[cache_key]

    if device == "auto":
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"

    if compute_type is None:
        compute_type = "float16" if device == "cuda" else "int8"

    print(f"Loading Whisper model '{model_size}' on {device} ({compute_type})...")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    _model_cache[cache_key] = model
    return model


def transcribe_chunk_whisper(chunk_path: str, translate: bool = False) -> str:
    model_size = os.getenv("WHISPER_MODEL", "tiny")
    model = load_whisper_model(model_size)

    task = "translate" if translate else "transcribe"

    # segments, info = model.transcribe(
    #     chunk_path,
    #     task=task,
    #     beam_size=1,
    #     vad_filter=True,
    # )
    segments, info = model.transcribe(chunk_path, task=task, beam_size=5, vad_filter=True)
    return " ".join(segment.text.strip() for segment in segments)



# ===== Skip re-downloading/re-chunking on rerun =====
def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        # Derive an expected output path pattern to check for existing chunks
        video_id = source.split("v=")[-1].split("&")[0]
        existing_chunks = sorted(glob.glob(os.path.join(DOWNLOAD_DIR, f"*{video_id}*_chunk_*.wav")))
        if existing_chunks:
            print(f"Found {len(existing_chunks)} existing chunk(s) — skipping download/chunking.")
            return existing_chunks

        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        base_name = os.path.splitext(os.path.basename(source))[0]
        existing_chunks = sorted(glob.glob(os.path.join(DOWNLOAD_DIR, f"{base_name}*_chunk_*.wav")))
        if existing_chunks:
            print(f"Found {len(existing_chunks)} existing chunk(s) — skipping conversion/chunking.")
            return existing_chunks

        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready - {len(chunks)} chunk(s) created.")
    return chunks


# ===== Sarvam AI (cloud) =====
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v3")

def transcribe_chunk_sarvam(chunk_path: str, mode: str = "translate") -> str:
    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY not set in .env")

    headers = {"API-Subscription-Key": SARVAM_API_KEY}
    endpoint = "https://api.sarvam.ai/speech-to-text"

    audio = AudioSegment.from_wav(chunk_path)
    sub_chunk_ms = 29 * 1000
    full_text = ""

    for start in range(0, len(audio), sub_chunk_ms):
        sub_audio = audio[start:start + sub_chunk_ms]
        sub_path = f"{chunk_path}_sub_{start}.wav"
        sub_audio.export(sub_path, format="wav")

        with open(sub_path, "rb") as f:
            files = {"file": (os.path.basename(sub_path), f, "audio/wav")}
            data = {"model": SARVAM_MODEL, "mode": mode}
            response = requests.post(endpoint, headers=headers, files=files, data=data)

        os.remove(sub_path)

        if response.status_code != 200:
            print("Sarvam API error response:", response.text)
        response.raise_for_status()

        full_text += response.json().get("transcript", "") + " "

    return full_text.strip()


# ===== Unified interface, driven by `language` =====

def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    language: "english"  -> Whisper, no translation needed
              "hinglish"  -> Whisper, handles code-switched audio natively
              "hindi"     -> Sarvam (Hindi-optimized) + translate to English
    """
    language = language.lower()

    if language == "hindi":
        hindi_text = transcribe_chunk_sarvam(chunk_path)
        return GoogleTranslator(source="hi", target="en").translate(hindi_text)
    elif language in ("english", "hinglish"):
        # translate=True is harmless for pure English, and correctly
        # normalizes Hinglish speech to English text
        return transcribe_chunk_whisper(chunk_path, translate=(language == "hinglish"))
    else:
        raise ValueError(f"Unknown language: {language}. Use 'english', 'hindi', or 'hinglish'.")


def transcribe_all(chunks: list, language: str = "english") -> str:
    full_transcript = ""

    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)} ({language})...")
        text = transcribe_chunk(chunk, language=language)
        full_transcript += text + " "

    print("Transcription completed.")
    return full_transcript.strip()


# ===== Optional: auto-detect language instead of hardcoding =====

def detect_language(chunk_path: str) -> tuple:
    model = load_whisper_model(os.getenv("WHISPER_MODEL", "tiny"))
    # segments, info = model.transcribe(chunk_path, task="transcribe", beam_size=1)
    segments, info = model.transcribe(chunk_path, task=task, beam_size=5, vad_filter=True)
    return info.language, info.language_probability