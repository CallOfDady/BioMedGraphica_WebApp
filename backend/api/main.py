# backend/api/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.api import processing
from backend.config import Config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: validate configuration
    try:
        Config.validate_config()
        print(f"✅ Database path validated: {Config.DATABASE_PATH}")
        print(f"✅ Backend configuration loaded successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print(f"💡 Please check your environment variables or create missing directories")
        raise
    
    yield
    
    # Shutdown: cleanup if needed
    print("🔄 Backend shutting down...")

app = FastAPI(
    title="BioMedGraphica Backend API",
    description="Backend API for BioMedGraphica Data Integration",
    version="1.0.0",
    lifespan=lifespan
)

# Mount your processing routes
app.include_router(processing.router, prefix="/api")

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "BioMedGraphica Backend API is running"}

# To run the app, use:
# uvicorn backend.api.main:app --reload