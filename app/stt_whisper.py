# app/stt_whisper.py
from __future__ import annotations
import os, tempfile
from typing import Optional, Dict, Any, Iterable
from faster_whisper import WhisperModel

# ---- Runtime options via env vars ----
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "tiny")  # tiny, base, small, medium, large-v3
WHISPER_DEVICE     = os.getenv("WHISPER_DEVICE", "cpu")       # "cpu" or "cuda"
# Good CPU default; if GPU w/ half precision: "float16"
WHISPER_COMPUTE    = os.getenv("WHISPER_COMPUTE", "int8")     # int8 | int8_float16 | float32 | float16

# Lazy-load singleton
_model: Optional[WhisperModel] = None
def get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE,
            download_root=os.getenv("WHISPER_CACHE_DIR"),  # optional
        )
    return _model

def _save_temp_audio(name_hint: str, data: bytes) -> str:
    # Try to preserve extension for ffmpeg probing; fall back to .wav
    ext = ".wav"
    for cand in (".mp3",".wav",".m4a",".ogg",".webm",".flac",".aac"):
        if name_hint.lower().endswith(cand):
            ext = cand
            break
    f = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    f.write(data); f.flush(); f.close()
    return f.name

def transcribe_whisper(
    src_bytes: bytes,
    filename_hint: str = "audio.wav",
    language: Optional[str] = None,     # e.g., "en", "fil", "tl"
    translate: bool = False,            # if True: task="translate"
    vad: bool = True,
    beam_size: int = 5,
    best_of: int = 5,
) -> Dict[str, Any]:
    """
    Returns {"text": str, "language": str, "segments": [...], "duration": float}
    """
    tmp_path = _save_temp_audio(filename_hint, src_bytes)
    try:
        task = "translate" if translate else "transcribe"
        segments, info = get_model().transcribe(
            tmp_path,
            language=language,           # None = auto-detect
            task=task,
            vad_filter=vad,
            vad_parameters={"min_silence_duration_ms": 500},
            beam_size=beam_size,
            best_of=best_of,
        )
        seg_list = []
        full_text = []
        for s in segments:
            seg_list.append({
                "start": float(s.start),
                "end":   float(s.end),
                "text":  s.text.strip()
            })
            if s.text:
                full_text.append(s.text.strip())
        return {
            "text": " ".join(full_text).strip(),
            "language": info.language,
            "duration": float(info.duration),
            "segments": seg_list
        }
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
