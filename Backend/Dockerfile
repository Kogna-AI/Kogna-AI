# ---- Base Image ----
FROM python:3.11-slim

# ---- Set Working Directory ----
WORKDIR /app

# ---- Copy and Install Dependencies (Already good) ----
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# ---- Create Non-Root User (SECURITY FIX) ----
RUN adduser --disabled-password --no-create-home appuser
USER appuser
# ---------------------------------------------

# ---- Copy Application Code ----
# Ensure non-root user can read files (optional, but good practice)
COPY --chown=appuser:appuser . .

# ---- Expose Port ----
EXPOSE 8000

# ---- Run Command (PERFORMANCE FIX) ----
# Use Gunicorn with Uvicorn worker class for production. 
# --workers 4 or the recommended formula (2 * CPU cores + 1)
# You can override this in ECS Task Definition if needed, but this is a better default.
CMD ["/usr/local/bin/gunicorn", "main:app", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "4"]