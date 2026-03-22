FROM python:3.9-slim

WORKDIR /attacks

# Install tools needed for container attacks
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    netcat-traditional \
    procps \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy attack scripts
COPY *.py .

# Keep container running
CMD ["tail", "-f", "/dev/null"]
