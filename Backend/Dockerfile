# Start with an official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first for layer caching
COPY requirements/agents.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r agents.txt

# Copy the rest of your backend application code
# This will copy the 'ai_agent_folder', '.env', etc. into /app
COPY . .

# *** IMPORTANT CHANGE HERE ***
# Specify the command to run when the container starts.
# We now need to point to the script inside its subfolder.
CMD ["python", "Ai_agents/Orchestrator.py"]