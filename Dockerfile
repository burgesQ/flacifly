# flacifly — slim, multi-arch (linux/amd64 + linux/arm64) OCI image for a Raspberry Pi.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    XDG_DATA_HOME=/data \
    XDG_STATE_HOME=/data

# ffmpeg does the FLAC transcode; curl/unzip bootstrap Deno; ca-certificates for HTTPS.
RUN apt-get update \
 && apt-get install --no-install-recommends -y ffmpeg ca-certificates curl unzip \
 && rm -rf /var/lib/apt/lists/*

# Deno: JavaScript runtime yt-dlp uses to solve YouTube's signature / n-challenge.
# Without a JS runtime, YouTube exposes only thumbnails and every audio download fails.
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh \
 && deno --version

WORKDIR /app
COPY core ./core
COPY fetcher ./fetcher
COPY tagger ./tagger

# Install core first so fetcher/tagger resolve their local "core" dependency
# (the uv workspace sources are ignored by pip; core/ satisfies it once installed).
RUN pip install --no-cache-dir ./core \
 && pip install --no-cache-dir ./fetcher ./tagger

RUN useradd --create-home --uid 1000 flacifly \
 && mkdir -p /music /data /config \
 && chown -R flacifly:flacifly /music /data /config
USER flacifly

VOLUME ["/music", "/data", "/config"]

# Safe default: no-op unless a real --mode is provided (mirrors sosound-tools' -m 3).
CMD ["flacifly-fetch", "--mode", "off", "--download-root", "/music"]
