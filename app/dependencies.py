# app/dependencies.py
from app.services.indexing import IndexingService
from app.services.retrieval import RetrievalService
from app.config import settings
from fastapi import Depends, HTTPException, status
from langchain_chroma import Chroma
from app.utils.ollama_embed import OllamaEmbedding
import chromadb

def get_vector_store():
    """Create and return a Chroma vector store instance."""
    try:
        embedding_function = OllamaEmbedding()
        client = chromadb.PersistentClient(path=settings.chroma_db_path)
        return Chroma(
            client=client,
            collection_name=settings.chroma_collection_name,
            embedding_function=embedding_function
        )
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize vector store"
        )

def get_indexing_service(vector_store: Chroma = Depends(get_vector_store)):
    return IndexingService(vector_store)

def get_retrieval_service(vector_store: Chroma = Depends(get_vector_store)):
    return RetrievalService(vector_store)
