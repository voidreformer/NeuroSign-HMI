# ==============================================================================
# NeuroSign-HMI Max: Production Docker Environment for Arduino App Lab (UNO Q)
# Base: Debian Bookworm Slim with OpenCV, TensorFlow Lite GPU Delegates, & Piper TTS
# ==============================================================================

FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system utilities, GStreamer, ALSA audio, and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    python3-numpy \
    python3-opencv \
    alsa-utils \
    libasound2-dev \
    espeak-ng \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    v4l-utils \
    wget \
    curl \
    msgpack-python \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir --break-system-packages \
    mediapipe \
    tflite-runtime \
    pyserial \
    msgpack-rpc-python

# Set working directory
WORKDIR /app

# Copy application files
COPY ./app_mpu /app/app_mpu
COPY ./models /app/models

# Expose IPC socket mount point
VOLUME ["/var/run/arduino-router.sock"]

CMD ["python3", "/app/app_mpu/main_orchestrator.py"]
