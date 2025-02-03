from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from app.models.schemas import QuestionRequest, AnswerResponse, IngestResponse
from app.dependencies import get_retrieval_service, get_indexing_service, get_db
from app.services.retrieval import RetrievalService
from app.services.indexing import IndexingService
from sqlalchemy.orm import Session
from typing import List
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
    db: Session = Depends(get_db),
):
    """
    Ask a question within a chat context.

    This endpoint allows you to ask a question to a specific agent within a chat session.
    The chat history is used to provide context for the question, and the response is
    generated using the RAG pattern.

    Args:
        agent_id: The ID of the agent.
        chat_id: The ID of the chat session.
        request: The question request containing the question text.

    Returns:
        An AnswerResponse containing the answer and sources.
    """
    # Retrieve chat history
    chat_history = await retrieval_service.get_chat_history(agent_id, chat_id, db)
    
    # Append the new question to the chat history
    chat_history.append(request.question)
    
    # Generate a context-aware prompt
    context = "\n".join(chat_history)
    response = await retrieval_service.get_answer(context)
    
    # Save the new question and answer to the chat history
    await retrieval_service.save_chat_message(agent_id, chat_id, request.question, db)
    await retrieval_service.save_chat_message(agent_id, chat_id, response.answer, db)
    
    return AnswerResponse(
        answer=response.answer,
        sources=response.sources
    )

@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(
    url: str = Form(...),
    indexing_service: IndexingService = Depends(get_indexing_service),
):
    """
    Ingest content from a URL.

    This endpoint allows you to ingest content from a specified URL into the system's
    knowledge base.

    Args:
        url: The URL of the content to ingest.

    Returns:
        An IngestResponse indicating the success of the operation and the source URL.
    """
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
    """
    Ingest content from a PDF file.

    This endpoint allows you to upload and ingest content from a PDF file into the
    system's knowledge base.

    Args:
        file: The PDF file to ingest.

    Returns:
        An IngestResponse indicating the success of the operation and the source filename.
    """
    temp_dir = "/tmp"
    file_path = os.path.join(temp_dir, file.filename)
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
    """
    Ingest raw text content.

    This endpoint allows you to ingest raw text content into the system's knowledge base.

    Args:
        text: The text content to ingest.
        title: The title of the text content.

    Returns:
        An IngestResponse indicating the success of the operation and the source title.
    """
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