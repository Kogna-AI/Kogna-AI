# Kogna-AI
Building super dashboard for executives to make faster and better decisions

## Table of Contents
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Running the Application](#running-the-application)
- [Environment Configuration](#environment-configuration)

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.8+** - For running the backend server
- **Node.js 18+** and **npm** - For running the frontend application
- **Git** - For version control

## Project Structure

```
Kogna-AI/
├── Backend/          # FastAPI backend server
│   ├── api.py        # Main API endpoints
│   ├── main.py       # Application entry point
│   ├── requirements.txt
│   └── start_server.bat
└── frontend/         # Next.js frontend application
    ├── src/
    ├── package.json
    └── ...
```

## Backend Setup

### 1. Navigate to the Backend directory

```bash
cd Backend
```

### 2. Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the `Backend` directory with the required configuration:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# API Keys (if needed)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
SERPAPI_API_KEY=your_serpapi_api_key

# Database Configuration
DATABASE_URL=your_database_url
```

### 5. Start the backend server

**Option 1: Using the batch file (Windows)**
```bash
start_server.bat
```

**Option 2: Using uvicorn directly**
```bash
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The backend server will run on **http://localhost:8000**

## Frontend Setup

### 1. Navigate to the frontend directory

```bash
cd frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment variables

Create a `.env.local` file in the `frontend` directory:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Start the development server

```bash
npm run dev
```

The frontend will run on **http://localhost:3000**

## Running the Application

To run both backend and frontend together:

### Windows Users

1. **Terminal 1 - Backend:**
   ```bash
   cd Backend
   venv\Scripts\activate
   start_server.bat
   ```

2. **Terminal 2 - Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

### macOS/Linux Users

1. **Terminal 1 - Backend:**
   ```bash
   cd Backend
   source venv/bin/activate
   python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Terminal 2 - Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

### Access the Application

- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs (Swagger UI)

## Environment Configuration

### Required API Keys

The application uses several AI and data services. You'll need to obtain API keys from:

- **Supabase** - Database and authentication
- **OpenAI** - AI agent capabilities
- **Anthropic (Claude)** - AI agent capabilities
- **Google Gemini** - AI agent capabilities
- **SerpAPI** - Search functionality

### Configuration Files

- `Backend/.env` - Backend environment variables
- `frontend/.env.local` - Frontend environment variables

Make sure to never commit these files to version control.

## Development Commands

### Backend
- `python -m uvicorn api:app --reload` - Start with hot reload
- `pytest` - Run tests

### Frontend
- `npm run dev` - Start development server with Turbopack
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run linter
- `npm run format` - Format code


## Support

For issues and questions, please open an issue or pull request in the GitHub repository.