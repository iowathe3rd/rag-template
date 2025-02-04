# app/models/schemas.py
from pydantic import BaseModel, Field, UUID4
from typing import List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Chat(BaseModel):
    title: str = Field(..., max_length=255)
    messages: List[ChatMessage] = Field(default_factory=list)