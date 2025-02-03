from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from app.models.schemas import QuestionRequest, AnswerResponse, IngestResponse
from app.dependencies import get_retrieval_service, get_indexing_service
from app.services.retrieval import RetrievalService
from app.services.indexing import IndexingService
import logging
import os
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/agents/{agent_id}/chats/{chat_id}/ask", response_model=AnswerResponse)
async def ask_question(
    agent_id: str,
    chat_id: str,
    request: QuestionRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """Ask a question within a chat context."""
    response = await retrieval_service.get_answer(
        question=request.question,
        chat_id=chat_id
    )
    
    return AnswerResponse(
        answer=response.answer,
        sources=response.sources,
        metadata=response.metadata
    )

@router.post("/agents/{agent_id}/ingest/url", response_model=IngestResponse)
async def ingest_url(
    agent_id: str,
    url: str = Form(...),
    indexing_service: IndexingService = Depends(get_indexing_service),
):
    """Ingest content from URL into agent-specific knowledge base."""
    try:
        metadata = await indexing_service.index_content(
            source=url,
            source_type="web",
            metadata={"source_type": "url", "url": url, "agent_id": agent_id}
        )
        return IngestResponse(
            success=True,
            source=url,
            document_hash=metadata.document_hash
        )
    except Exception as e:
        logger.error(f"URL ingestion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/agents/{agent_id}/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(
    agent_id: str,
    file: UploadFile = File(...),
    indexing_service: IndexingService = Depends(get_indexing_service),
):
    """
    Ingest PDF content into agent-specific knowledge base.
    
    Args:
        agent_id: The ID of the agent to associate the content with
        file: The PDF file to ingest
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )
        
    temp_dir = settings.temp_file_path
    file_path = os.path.join(temp_dir, file.filename)
    
    try:
        os.makedirs(temp_dir, exist_ok=True)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        metadata = await indexing_service.index_content(
            source=file_path,
            source_type="pdf",
            metadata={
                "source_type": "pdf",
                "filename": file.filename,
                "agent_id": agent_id
            }
        )
        return IngestResponse(
            success=True,
            source=file.filename,
            document_hash=metadata.document_hash
        )
    except Exception as e:
        logger.error(f"PDF ingestion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/agents/{agent_id}/ingest/text", response_model=IngestResponse)
async def ingest_text(
    agent_id: str,
    text: str = Form(...),
    title: str = Form(...),
    indexing_service: IndexingService = Depends(get_indexing_service),
):
    """
    Ingest raw text content into agent-specific knowledge base.
    
    Args:
        agent_id: The ID of the agent to associate the content with
        text: The text content to ingest
        title: The title of the text content
    """
    try:
        metadata = await indexing_service.index_content(
            source=text,
            source_type="text",
            metadata={
                "source_type": "text",
                "title": title,
                "source": f"text-{title}",
                "agent_id": agent_id
            }
        )
        return IngestResponse(
            success=True,
            source=title,
            document_hash=metadata.document_hash
        )
    except Exception as e:
        logger.error(f"Text ingestion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )