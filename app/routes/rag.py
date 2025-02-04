from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from app.schemas.api import QuestionRequest, AnswerResponse, IngestResponse
from app.dependencies import get_retrieval_service, get_indexing_service
from app.services.rag.retrieval import RetrievalService
from app.services.rag.indexing import IndexingService
import logging
import os
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db

# Initialize router and logger
router = APIRouter()
logger = logging.getLogger(__name__)

# Question & Answer Endpoint
@router.post("/agents/{agent_id}/chats/{chat_id}/ask", response_model=AnswerResponse)
async def ask_question(
    chat_id: str,
    request: QuestionRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    Process a question within a specific chat context.
    
    Args:
        chat_id: Unique identifier for the chat session
        request: Contains the question text and any additional parameters
        retrieval_service: Service for retrieving and generating answers
        
    Returns:
        AnswerResponse containing the generated answer, sources, and metadata
        
    Raises:
        HTTPException: If answer generation fails
    """
    response = await retrieval_service.get_answer(
        question=request.question,
        chat_id=chat_id
    )
    
    return AnswerResponse(
        answer=response.answer,
        sources=response.sources,
        metadata=response.metadata
    )

# URL Content Ingestion Endpoint
@router.post("/agents/{agent_id}/ingest/url", response_model=IngestResponse)
async def ingest_url(
    agent_id: str,
    url: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest content from a URL into an agent's knowledge base.
    
    Args:
        agent_id: Unique identifier for the agent
        url: Web URL to scrape and ingest
        indexing_service: Service for content indexing operations
        
    Returns:
        IngestResponse with success status and document tracking info
        
    Raises:
        HTTPException: If URL ingestion fails
    """
    indexing_service: IndexingService = Depends(get_indexing_service(agent_id))

    try:
        metadata = await indexing_service.index_content(
            source=url,
            source_type="web",
            metadata={"source_type": "url", "url": url},
            db=db
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

# PDF Document Ingestion Endpoint
@router.post("/agents/{agent_id}/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(
    agent_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a PDF document into an agent's knowledge base.
    
    Args:
        agent_id: Unique identifier for the agent
        file: Uploaded PDF file
        indexing_service: Service for content indexing operations
        
    Returns:
        IngestResponse with success status and document tracking info
        
    Raises:
        HTTPException: If file is not PDF or ingestion fails
    """
    # Validate file extension
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )
    
    # Setup temporary file path    
    temp_dir = settings.temp_file_path
    file_path = os.path.join(temp_dir, file.filename)

    indexing_service: IndexingService = Depends(get_indexing_service(agent_id))

    try:
        # Ensure temp directory exists and save file
        os.makedirs(temp_dir, exist_ok=True)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process and index the PDF
        metadata = await indexing_service.index_content(
            source=file_path,
            source_type="pdf",
            metadata={
                "source_type": "pdf",
                "filename": file.filename,
            },
            db=db
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
        # Cleanup temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

# Raw Text Ingestion Endpoint
@router.post("/agents/{agent_id}/ingest/text", response_model=IngestResponse)
async def ingest_text(
    agent_id: str,
    text: str = Form(...),
    title: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest raw text content into an agent's knowledge base.
    
    Args:
        agent_id: Unique identifier for the agent
        text: Raw text content to ingest
        title: Title/identifier for the text content
        indexing_service: Service for content indexing operations
        
    Returns:
        IngestResponse with success status and document tracking info
        
    Raises:
        HTTPException: If text ingestion fails
    """

    indexing_service: IndexingService = Depends(get_indexing_service(agent_id))

    try:
        metadata = await indexing_service.index_content(
            source=text,
            source_type="text",
            metadata={
                "source_type": "text",
                "title": title,
                "source": f"text-{title}",
            },
            db=db
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