from fastapi import FastAPI
from core.config import setup_cors
from routers import (
    organizations, users, teams, objectives,
    metrics, insights, recommendations, actions,ai_pipeline
)

app = FastAPI(
    title="KognaDash API",
    description="AI-Powered Strategic Management Dashboard",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS setup
setup_cors(app)

# Register routers
app.include_router(organizations.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(objectives.router)
app.include_router(metrics.router)
app.include_router(insights.router)
app.include_router(recommendations.router)
app.include_router(actions.router)
app.include_router(ai_pipeline.router)

@app.get("/")
def root():
    return {
        "status": "healthy",
        "service": "KognaDash API",
        "version": "2.0.0",
        "docs": "/api/docs"
    }
