# ---- Stage 1: build the React frontend -------------------------------------
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ---- Stage 2: Python API + self-building ML artifacts ----------------------
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cupcast/ cupcast/
COPY scripts/ scripts/
COPY web/ web/
COPY --from=frontend /build/dist frontend/dist

# Reproducible MLOps: the image builds its own artifacts from public data —
# download history, train the model, simulate the tournament, fetch forecasts
# and squads. No secrets, no API keys.
RUN python scripts/download_data.py \
    && python -m cupcast.train \
    && python -m cupcast.simulate 5000 \
    && python -m cupcast.weather \
    && python scripts/build_squads.py

# HF Spaces expects 7860; Render injects $PORT
EXPOSE 7860
CMD ["sh", "-c", "uvicorn cupcast.api:app --host 0.0.0.0 --port ${PORT:-7860}"]
