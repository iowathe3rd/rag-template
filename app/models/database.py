from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from chromadb import Collection, HttpClient
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

Base = declarative_base()

class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    chats = relationship("Chat", back_populates="agent", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_agent_name', name),
    )

class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'), nullable=False)
    title = Column(String(255), nullable=False)
    chat_metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("Agent", back_populates="chats")
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_chat_agent_id', agent_id),
    )

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chats.id'), nullable=False)
    role = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chat = relationship("Chat", back_populates="messages")

    __table_args__ = (
        Index('idx_message_chat_id', chat_id),
    )

_chroma_client = None

class ChromaManager:
    def __init__(self):
        global _chroma_client
        if _chroma_client is None:
            _chroma_client = HttpClient(
                host=settings.chroma.host,
                port=settings.chroma.port,
            )
            self.client = _chroma_client
        
    async def get_or_create_collection(self, name: str) -> Collection:
        return await self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    async def delete_collection(self, name: str) -> None:
        await self.client.delete_collection(name=name)

chroma_manager = ChromaManager() 