from fastapi import APIRouter, Depends, UploadFile, File, Form
from app.models.schemas import QuestionRequest, AnswerResponse, IngestResponse
from app.dependencies import get_retrieval_service, get_indexing_service
from app.services.retrieval import RetrievalService
from app.services.indexing import IndexingService
from typing import List

router = APIRouter()

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
    file_path = f"temp/{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    success = await indexing_service.index_content(
        source=file_path,
        source_type="pdf",
        metadata={"source_type": "pdf", "filename": file.filename}
    )
    return IngestResponse(success=success, source=file.filename)

@router.post("/ingest/text", response_model=IngestResponse)
async def ingest_text(
    text: str = Form(...),
    title: str = Form(...),
    indexing_service: IndexingService = Depends(get_indexing_service),
):
    """Ingest raw text content."""
    success = await indexing_service.index_content(
        source=text,
        source_type="text",
        metadata={"source_type": "text", "title": title}
    )
    return IngestResponse(success=success, source=title)