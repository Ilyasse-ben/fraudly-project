FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHROMA_HTTP_HOST=chroma
ENV CHROMA_HTTP_PORT=8000
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENV ANALYTICS_SERVICE_BASE_URL=http://analytics-service:8081/api/analytics

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m appuser

# Copy requirements and install
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy application code and set ownership to appuser
COPY --chown=appuser:appuser . .

# Ensure the app directory is owned by appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]