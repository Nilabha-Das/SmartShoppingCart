FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first so they stay cached until requirements change
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --default-timeout=120 --retries=10 -r requirements.txt

# Copy only the application code after dependencies are installed
COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]