# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class Agent(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str]
