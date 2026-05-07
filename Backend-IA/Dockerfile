FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR and PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy application code
COPY . .

# Environment defaults (overridable via docker-compose)
ENV PYTHONUNBUFFERED=1
ENV CHROMA_HTTP_HOST=chroma
ENV CHROMA_HTTP_PORT=8000
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENV ANALYTICS_SERVICE_BASE_URL=http://analytics-service:8081/api/analytics

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
