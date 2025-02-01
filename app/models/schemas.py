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

class Agent(BaseModel):
    id: str
    knowledge_base_path: str

class Chat(BaseModel):
    id: str
    agent_id: str
    messages: List[str] = []