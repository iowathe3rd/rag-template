# app/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    sources: List[str]

class IngestResponse(BaseModel):
    success: bool
    source: str