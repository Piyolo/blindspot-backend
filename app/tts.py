# app/tts.py
from io import BytesIO
from gtts import gTTS

def synthesize_mp3(text: str, lang: str = "en", slow: bool = False) -> bytes:
    """
    TTS using Google gTTS (online). Returns MP3 bytes.
    """
    if not text or not text.strip():
        raise ValueError("Text is empty")
    mp3 = BytesIO()
    tts = gTTS(text=text, lang=lang, slow=slow)
    tts.write_to_fp(mp3)
    mp3.seek(0)
    return mp3.read()
