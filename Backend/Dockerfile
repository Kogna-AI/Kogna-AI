# ============================================
# AWS-Optimized FastAPI Backend Dockerfile
# Fixed for CrewAI permissions
# ============================================

# ---- Base Image ----
FROM python:3.11-slim

# ---- Set Working Directory ----
WORKDIR /app

# ---- Copy and Install Python Dependencies ----
COPY requirements.txt .

# Install dependencies as root
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Create Non-Root User with Home Directory ----
# CrewAI needs a writable home directory for ChromaDB storage
RUN adduser --disabled-password --gecos "" appuser && \
    mkdir -p /home/appuser/.local/share && \
    chown -R appuser:appuser /home/appuser

# ---- Copy Application Code ----
COPY --chown=appuser:appuser . .

# ---- Switch to Non-Root User ----
USER appuser

# ---- Set Environment Variables for CrewAI ----
# Tell CrewAI to use /app for storage instead of home directory
ENV HOME=/home/appuser
ENV CREWAI_STORAGE_DIR=/app/.crewai

# Create CrewAI storage directory with proper permissions
USER root
RUN mkdir -p /app/.crewai && chown -R appuser:appuser /app/.crewai
USER appuser

# ---- Expose Port ----
EXPOSE 8000

# ---- Health Check ----
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

# ---- Run Command ----
CMD ["gunicorn", "main:app", \
     "--bind", "0.0.0.0:8000", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
