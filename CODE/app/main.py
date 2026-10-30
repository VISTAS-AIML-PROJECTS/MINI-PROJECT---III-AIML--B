"""
GenVoice 2.0 - Main FastAPI Application

Entry point for the backend API server
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from .config import settings
from .database import init_db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered elderly monitoring and family coordination system",
    version="2.0.0",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS middleware (allow mobile app to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()

    logger.info(f"➡️  {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"⬅️  {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}s)")

    return response


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GenVoice 2.0 API",
        "version": "2.0.0",
        "status": "running",
        "docs": f"{settings.API_V1_PREFIX}/docs"
    }


@app.get(f"{settings.API_V1_PREFIX}/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "genvoice-api",
        "version": "2.0.0",
        "features": {
            "ai_analysis": settings.ENABLE_AI_ANALYSIS,
            "sms_alerts": settings.ENABLE_SMS_ALERTS,
            "background_jobs": settings.ENABLE_BACKGROUND_JOBS
        }
    }


# Import and include routers
from .api_routes import router as api_router
app.include_router(api_router, prefix=f"{settings.API_V1_PREFIX}", tags=["Conversations"])


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    logger.info("🚀 Starting GenVoice 2.0 API...")

    # Create database tables
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

    # Initialize background jobs (if enabled)
    if settings.ENABLE_BACKGROUND_JOBS:
        # from .services.scheduler import start_scheduler
        # start_scheduler()
        logger.info("✅ Background jobs enabled (not implemented yet)")

    logger.info(f"✅ GenVoice API running on http://{settings.HOST}:{settings.PORT}")
    logger.info(f"📖 API docs: http://{settings.HOST}:{settings.PORT}{settings.API_V1_PREFIX}/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down GenVoice API...")

    # Stop background jobs
    if settings.ENABLE_BACKGROUND_JOBS:
        # from .services.scheduler import stop_scheduler
        # stop_scheduler()
        logger.info("✅ Background jobs stopped")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": str(exc) if settings.DEBUG else None
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )
