# app/dependencies.py
from app.services.indexing import IndexingService
from app.services.retrieval import RetrievalService
from app.config import settings
from fastapi import Depends, HTTPException, Header, status
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

def get_indexing_service():
    return IndexingService()

def get_retrieval_service():
    try:
        vector_store = Chroma(
            persist_directory=settings.chroma_db_path,
            embedding_function=OpenAIEmbeddings(api_key=settings.openai_api_key)
        )
        return RetrievalService(vector_store)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

def verify_api_key(api_key: str = Header(None)):
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key