FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/

# Create non-root user (but we'll run as root for vulnerability)
RUN useradd -m -u 1000 appuser

# Intentionally run as root (vulnerable)
USER root

EXPOSE 80

CMD ["python", "app.py"]
