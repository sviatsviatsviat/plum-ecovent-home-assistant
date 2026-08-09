FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        ffmpeg \
        libturbojpeg0 \
    && rm -rf /var/lib/apt/lists/*
