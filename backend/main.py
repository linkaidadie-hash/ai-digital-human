"""
AI Digital Human - FastAPI Backend Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import assets, templates, tts, subtitle, render, projects, settings

# Initialize FastAPI app
app = FastAPI(
    title="AI Digital Human API",
    description="Backend API for AI Digital Human video generation system",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(assets.router)
app.include_router(templates.router)
app.include_router(tts.router)
app.include_router(subtitle.router)
app.include_router(render.router)
app.include_router(projects.router)
app.include_router(settings.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print("[API] AI Digital Human Backend started successfully")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "AI Digital Human API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)