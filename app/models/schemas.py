# app/models/schemas.py
from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str
    max_tokens: int = 512

class AnswerResponse(BaseModel):
    answer: str
    sources: list[str]