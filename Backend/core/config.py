from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not found")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# --- FIX: Define the allowed origins for local development ---
# The browser accesses the backend via the host's exposed port (8000), 
# so we need to allow the host's addresses, running on port 3000.
ALLOWED_ORIGINS = [
    # Local Development access points (Host machine)
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    
    # You may also need to allow the specific IP of your Docker bridge 
    # network if the connection is erratic (less common, but safe to include)
    # The IP 172.18.0.x is an example of an internal docker network range.
    # To be safe, adding "*" for development is a quick fix, but specific URLs are better.
    # For a quick fix, you can use ["*"], but for slightly better practice:
    # "http://0.0.0.0:3000",
]
# If you need to allow all connections during dev (less secure, but quick):
# ALLOWED_ORIGINS = ["*"]


def setup_cors(app: FastAPI):
    """
    Sets up the CORS middleware for the FastAPI application.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,  # Use the list defined above
        allow_credentials=True,         # Required if you use cookies or auth headers
        allow_methods=["*"],            # Allows all methods (GET, POST, HEAD, etc.)
        allow_headers=["*"],            # Allows all headers, including custom ones
    )