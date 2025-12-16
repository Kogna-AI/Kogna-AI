# main.py
# AWS-Compatible FastAPI Application for KognaDash API

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from core.config import setup_cors
from dotenv import load_dotenv
from datetime import datetime
import logging

from routers import (
    organizations, users, teams, objectives,
    metrics, insights, recommendations, actions,ai_pipeline,connectors,chat, auth
)

# Load environment variables
load_dotenv()

# Setup logging for AWS CloudWatch
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="KognaDash API",
    description="AI-Powered Strategic Management Dashboard",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS setup (reads from ALLOWED_ORIGINS environment variable)
setup_cors(app)

# ==================== REGISTER ROUTERS ====================

app.include_router(connectors.connect_router)   
app.include_router(connectors.callback_router)
app.include_router(organizations.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(objectives.router)
app.include_router(metrics.router)
app.include_router(insights.router)
app.include_router(recommendations.router)
app.include_router(actions.router)
app.include_router(ai_pipeline.router)
app.include_router(chat.router)
app.include_router(auth.router)

# ==================== ROOT ENDPOINT ====================

@app.get("/")
def root():
    """Root endpoint with basic service information"""
    return {
        "status": "healthy",
        "service": "KognaDash API",
        "version": "2.0.0",
        "docs": "/api/docs"
    }

# ==================== HEALTH CHECK ENDPOINTS ====================

@app.get("/health")
async def health_check():
    """
    Health check endpoint for AWS Load Balancer / ECS.
    
    AWS will ping this endpoint to verify the container is healthy.
    If this returns non-200 status, AWS will restart the container.
    
    This is CRITICAL for AWS deployment.
    """
    return {
        "status": "healthy",
        "service": "KognaDash API",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check including database connectivity.
    Useful for monitoring and debugging.
    """
    checks = {
        "api": "healthy",
        "database": "unknown",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "KognaDash API",
        "version": "2.0.0"
    }
    
    # Check database connectivity
    try:
        from core.database import SessionLocal
        db = SessionLocal()
        # Simple query to verify DB connection
        db.execute("SELECT 1")
        db.close()
        checks["database"] = "healthy"
        logger.info("Database health check: healthy")
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
        logger.error(f"Database health check failed: {e}")
        # Return 503 Service Unavailable if database is down
        return JSONResponse(status_code=503, content=checks)
    
    return checks

# ==================== STARTUP/SHUTDOWN EVENTS ====================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("=" * 50)
    logger.info("Starting KognaDash API v2.0.0")
    logger.info("Environment: Production-ready with AWS support")
    logger.info("=" * 50)

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down KognaDash API")

# ==================== GLOBAL EXCEPTION HANDLER ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    Logs errors and returns generic response to client.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        }
    )

# ==================== FOR LOCAL DEVELOPMENT ====================
# 👇 只需要引入这几个 RBAC 相关的即可
from fastapi import Depends
from core.permissions import require_permission, UserContext, get_user_context

# ==========================================
# 场景 1：只有 Manager 或有权限的人能进
# ==========================================
@app.get("/test/protected/insights")
async def get_team_insights(
    user_ctx: UserContext = Depends(require_permission("insights", "read", "team"))
):
    return {
        "status": "Success",
        "message": "你有权访问这个接口！",
        "user": user_ctx.email,
        "role": user_ctx.role_name
    }

# ==========================================
# 场景 2：什么人都能进，但我需要知道你是谁
# ==========================================
@app.get("/test/public/whoami")
async def who_am_i(
    user_ctx: UserContext = Depends(get_user_context)
):
    return {
        "id": user_ctx.id,
        "role": user_ctx.role_name,
        "permissions": user_ctx.permissions
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Hot reload for development
        log_level="info"
    )