# app/routes/rag.py
from fastapi import APIRouter, Depends
from app.models.schemas import QuestionRequest, AnswerResponse
from app.dependencies import (
    get_retrieval_service,
    verify_api_key,
)
from app.services.retrieval import RetrievalService

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