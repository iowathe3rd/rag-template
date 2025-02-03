# app/models/schemas.py
from pydantic import BaseModel, Field, UUID4, validator
from typing import List, Dict, Any, Optional
from datetime import datetime

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    context: Optional[str] = Field(None, max_length=5000)

class AnswerResponse(BaseModel):
    answer: str
    sources: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class IngestResponse(BaseModel):
    success: bool
    source: str
    document_hash: str

class AgentConfig(BaseModel):
    model_name: str
    temperature: float = Field(ge=0.0, le=1.0)
    max_tokens: int = Field(ge=1)
    chunk_size: int = Field(ge=100)
    chunk_overlap: int = Field(ge=0)

class Agent(BaseModel):
    id: UUID4
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str]
    llm_config: Dict[str, Any]
    rag_config: Dict[str, Any]
    collection_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Chat(BaseModel):
    id: UUID4
    agent_id: UUID4
    title: str = Field(..., max_length=255)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True