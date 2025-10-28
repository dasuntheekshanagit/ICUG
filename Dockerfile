FROM python:3.13-slim

# Install system dependencies required by LightGBM (OpenMP runtime)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

ENV PORT=8000
CMD gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY:-2} --timeout 60
