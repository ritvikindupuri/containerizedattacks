FROM ubuntu:20.04

# Install tools that can be abused
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    netcat \
    nmap \
    python3 \
    python3-pip \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app.sh .
RUN chmod +x app.sh

# Run as root in privileged mode
USER root

CMD ["./app.sh"]
