from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, ALL_MODELS, GROQ_MODELS, OPENCODE_MODELS

# API Routers
from app.api import chat, search, settings as settings_router, ingest

# Initialize FastAPI
app = FastAPI(
    title="QA Search Bot API",
    description="RAG-powered QA Copilot with Groq and OpenCode integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(settings_router.router, prefix="/api", tags=["Settings"])
app.include_router(ingest.router, prefix="/api", tags=["Ingest"])


@app.get("/")
async def root():
    return {
        "message": "QA Search Bot API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/models")
async def get_models():
    return {
        "models": ALL_MODELS,
        "groq_models": GROQ_MODELS,
        "openai_models": OPENCODE_MODELS
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True
    )