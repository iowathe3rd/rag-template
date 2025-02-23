# app/dependencies.py
from logging import Logger
from app.services.indexing import IndexingService
from app.services.retrieval import RetrievalService
from app.config import settings
from fastapi import Depends, HTTPException, status
from langchain_chroma import Chroma
from langchain_together.embeddings import TogetherEmbeddings
from app.utils.ollama_embed import OllamaEmbedding
import chromadb
from sqlalchemy.orm import Session
from app.models.database import SessionLocal

def get_embedding_function():
    """Create and return an embedding function instance."""
    return TogetherEmbeddings(
        api_key=settings.togetherai_api_key,
        model=settings.embedding_model,
    )
    

def get_vector_store(agent_id: str):
    """Create and return a Chroma vector store instance for a specific agent."""
    try:
        agent = agents.get(agent_id)
        if not agent:
            raise ValueError("Agent not found")
        
        embedding_function = get_embedding_function()
        client = chromadb.PersistentClient(path=agent.knowledge_base_path)
        return Chroma(
            client=client,
            collection_name=settings.chroma_collection_name,
            embedding_function=embedding_function
        )
    except Exception as e:
        Logger.error(f"Failed to initialize vector store for agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize vector store"
        )

def get_indexing_service(vector_store: Chroma = Depends(get_vector_store)):
    return IndexingService(vector_store)

def get_retrieval_service(vector_store: Chroma = Depends(get_vector_store)):
    return RetrievalService(vector_store)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
