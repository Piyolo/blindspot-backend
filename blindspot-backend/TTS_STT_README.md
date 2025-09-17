
# Added TTS/STT to BlindSpot API

## New endpoints
- `POST /tts` — body JSON: `{ "text": "Hello", "lang": "en", "slow": false }` → returns MP3 audio
- `POST /stt` — multipart form: `file=@audio.m4a` (or mp3/wav) → returns transcription JSON

## Install
```
pip install -r requirements.txt
# System requirement:
#   ffmpeg must be installed and on PATH
```

## Run
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Test
```
curl -X POST http://127.0.0.1:8000/tts -H "Content-Type: application/json" -d '{"text":"Hello from BlindSpot!","lang":"en"}' --output hello.mp3

curl -X POST http://127.0.0.1:8000/stt -F file=@sample.wav
```

## Notes
- Environment var `WHISPER_MODEL` controls model size (default `base`). Options: `tiny`, `base`, `small`, `medium`, `large-v3`.
- On small servers, use `tiny` for speed: `set WHISPER_MODEL=tiny` (Windows) or `export WHISPER_MODEL=tiny` (Linux/macOS).
