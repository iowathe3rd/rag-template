from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid
from chromadb import Collection, PersistentClient
from app.config import settings
from typing import Optional

Base = declarative_base()

class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    llm_config = Column(JSON, nullable=False)
    rag_config = Column(JSON, nullable=False)
    chroma_collection_name = Column(String(255), unique=True, nullable=False)
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
    metadata = Column(JSON, default={})
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
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chat = relationship("Chat", back_populates="messages")

    __table_args__ = (
        Index('idx_message_chat_id', chat_id),
    )

class ChromaManager:
    def __init__(self):
        self.client = PersistentClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings={
                "chroma_client_auth_provider": "chromadb.auth.basic",
                "chroma_client_auth_credentials": settings.chroma_auth_credentials
            }
        )

    def get_or_create_collection(self, name: str) -> Collection:
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    def delete_collection(self, name: str) -> None:
        self.client.delete_collection(name=name)

chroma_manager = ChromaManager() 