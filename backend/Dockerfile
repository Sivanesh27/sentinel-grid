# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend Runtime & Full-Stack Server
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SENTINEL_DB_PATH=/app/sentinel.db \
    PORT=8000

WORKDIR /app

# Install system dependencies for OpenCV and video codecs
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Pre-cache YOLOv8 weights so container starts instantly without download latency
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Copy configuration and application source
COPY config /app/config
COPY backend /app/backend

# Copy built frontend assets from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Generate initial sample test videos if not present
RUN python /app/backend/scripts/generate_sample_videos.py

WORKDIR /app/backend

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
