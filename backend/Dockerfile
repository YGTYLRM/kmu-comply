FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt lives at repo root (context is repo root in docker-compose)
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Install Playwright chromium for PDF generation, into a path outside /app
# (docker-compose bind-mounts the host backend/ dir over /app, which would
# otherwise hide anything installed under /app) and outside root's home
# (unreadable once we switch to a non-root user below).
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers
RUN mkdir -p /opt/playwright-browsers && playwright install chromium --with-deps

COPY backend/ .

# Run as a non-root user. Note: docker-compose bind-mounts ./backend over
# /app, so file ownership there follows the host directory, not this chown —
# if you hit permission errors writing to data/ under the bind mount, match
# this UID/GID (1000:1000) on the host directory, or run without the mount.
RUN groupadd --system --gid 1000 appuser \
    && useradd --system --uid 1000 --gid appuser --no-create-home appuser \
    && chown -R appuser:appuser /app /opt/playwright-browsers

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
