# ---- Base Image ----
# Use an official, lightweight Python 3.11 "slim" image.
# This provides a good balance of size and having necessary tools.
FROM python:3.11-slim

# ---- Set Working Directory ----
# All commands will now run from inside /app
WORKDIR /app

# ---- Copy and Install Dependencies ----
# Copy *only* the requirements file first.
# This takes advantage of Docker's layer caching.
# If your code changes, Docker won't need to reinstall all your libraries.
COPY requirements.txt .

# Install the Python libraries
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# ---- Copy Application Code ----
# Now, copy all your application code (main.py, routers/, core/, etc.)
# The .dockerignore file will make sure .env and other junk is skipped.
COPY . .

# ---- Expose Port ----
# Tell Docker that the container will listen on port 8000.
EXPOSE 8000

# ---- Run Command ----
# This is the command to run your app in production.
# We use uvicorn to run the 'app' object from your 'main.py' file.
#
# --host 0.0.0.0: This is MANDATORY. It tells the app to listen for
#     connections from *outside* the container. The default (127.0.0.1) will fail.
# --port 8000: Matches the EXPOSE command.
#
# (We remove --reload because that's only for development.)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]