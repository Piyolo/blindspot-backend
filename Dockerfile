FROM python:3.10-slim

# System deps for audio decoding
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY app /app/app

# Faster-whisper defaults (CPU-friendly)
ENV WHISPER_DEVICE=cpu
ENV WHISPER_COMPUTE=int8
ENV WHISPER_MODEL_SIZE=tiny

# Render provides $PORT — bind to it
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
