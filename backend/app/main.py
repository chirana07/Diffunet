"""
FastAPI Application - Low-Light Image Enhancer Backend
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import enhance


# Ensure uploads directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    print("🚀 Low-Light Image Enhancer API starting...")
    print(f"📁 Upload directory: {os.path.abspath(UPLOAD_DIR)}")
    yield
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Low-Light Image Enhancer API",
    description="AI-Powered Low-Light Image Restoration and Quality Analyzer",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration - Allow Next.js frontend + Vercel + ngrok
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.ngrok-free\.app|https://.*\.ngrok\.io",  # Allow all Vercel + ngrok
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving uploaded images
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Register routes
app.include_router(enhance.router, prefix="/api", tags=["Enhancement"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Low-Light Image Enhancer API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "low-light-enhancer",
        "version": "1.0.0",
    }
