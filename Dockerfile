FROM python:3.13-slim

# No extra OS packages required for scikit-learn + joblib

WORKDIR /app

# Install Python dependencies first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

ENV PORT=8000 \
    WEB_CONCURRENCY=2
CMD ["sh", "./start.sh"]
