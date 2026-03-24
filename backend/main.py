"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import settings
from app.api.routes import router

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="B2B Product Categorization API",
    version="1.0.0",
    debug=settings.fastapi_debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "B2B Product Categorization API", "status": "running"}


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.fastapi_debug
    )
