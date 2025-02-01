# app/main.py
from fastapi import FastAPI
from app.routes import rag, agents
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="RAG Assistant API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rag.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}