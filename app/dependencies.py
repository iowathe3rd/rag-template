from logging import getLogger

import chromadb
from app.services.indexing import IndexingService
from app.services.retrieval import RetrievalService
from app.config import settings
from fastapi import Depends
from langchain_together.embeddings import TogetherEmbeddings
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = getLogger(__name__)

# Create PostgreSQL engine
engine = create_engine(
    settings.database_url,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Cache the embedding function to avoid recreating it for each request
_embedding_function = None

def get_embedding_function():
    """Create and return a cached embedding function instance."""
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = TogetherEmbeddings(
            api_key=settings.togetherai_api_key,
            model=settings.embedding_model,
        )
    return _embedding_function

def get_indexing_service(
    agent_id: str,
    db: Session = Depends(get_db)
) -> IndexingService:
    """Get agent-specific indexing service."""
    return IndexingService(agent_id=agent_id, db=db)

def get_retrieval_service(
    agent_id: str,
    db: Session = Depends(get_db)
) -> RetrievalService:
    """Get agent-specific retrieval service."""
    return RetrievalService(agent_id=agent_id, db=db)

_chroma_client = None

def get_chroma_client():
    """Create and return a cached Chroma client instance."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=settings.chroma.host,
            port=settings.chroma.port,
            settings=chromadb.Settings(
                chroma_client_auth_provider=settings.chroma.auth_provider,
                chroma_client_auth_credentials=settings.chroma.auth_credentials,
            )
        )
    return _chroma_client
