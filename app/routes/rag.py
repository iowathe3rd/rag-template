from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from app.models.schemas import QuestionRequest, AnswerResponse, IngestResponse
from app.dependencies import get_retrieval_service, get_indexing_service
from app.services.retrieval import RetrievalService
from app.services.indexing import IndexingService
from typing import List
import logging
import os
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    response = await retrieval_service.get_answer(request.question)
    return AnswerResponse(
        answer=response["answer"],
        sources=response["sources"]
    )

@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(
    url: str = Form(...),
    indexing_service: IndexingService = Depends(get_indexing_service),
):
    """Ingest content from a URL."""
    success = await indexing_service.index_content(
        source=url,
        source_type="web",
        metadata={"source_type": "url", "url": url}
    )
    return IngestResponse(success=success, source=url)

@router.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    indexing_service: IndexingService = Depends(get_indexing_service),
):
    """Ingest content from a PDF file."""
    os.makedirs(settings.temp_file_path, exist_ok=True)
    file_path = os.path.join(settings.temp_file_path, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        success = await indexing_service.index_content(
            source=file_path,
            source_type="pdf",
            metadata={"source_type": "pdf", "filename": file.filename}
        )
        return IngestResponse(success=success, source=file.filename)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/ingest/text", response_model=IngestResponse)
async def ingest_text(
    text: str = Form(...),
    title: str = Form(...),
    indexing_service: IndexingService = Depends(get_indexing_service),
):
    """Ingest raw text content."""
    try:
        success = await indexing_service.index_content(
            source=text,
            source_type="text",
            metadata={
                "source_type": "text",
                "title": title,
                "source": f"text-{title}"  # Add source identifier
            }
        )
        return IngestResponse(success=success, source=title)
    except Exception as e:
        logger.error(f"Text ingestion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )