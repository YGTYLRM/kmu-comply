FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt lives at repo root (context is repo root in docker-compose)
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Install Playwright chromium for PDF generation
RUN playwright install chromium --with-deps

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
