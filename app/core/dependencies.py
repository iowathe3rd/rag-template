from logging import getLogger

from app.services.rag.indexing.indexing_service import IndexingService
from app.services.rag.retrieval.retrieval_service import RetrievalService
from app.core.config import settings
from fastapi import Depends
from langchain_together.embeddings import TogetherEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.agent.manager import AgentManager
from app.services.chat.manager import ChatManager

logger = getLogger(__name__)


# Cache the embedding function to avoid recreating it for each request
_embedding_function = None

def get_embedding_function():
    """Create and return a cached embedding function instance."""
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = TogetherEmbeddings(
            api_key=settings.togetherai_api_key,
            model=settings.embedding_model,
        )
    return _embedding_function

def get_indexing_service(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
) -> IndexingService:
    """Get agent-specific indexing service."""
    return IndexingService(agent_id=agent_id, db=db)

def get_retrieval_service(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
) -> RetrievalService:
    """Get agent-specific retrieval service."""
    return RetrievalService(agent_id=agent_id, db=db)

def get_agent_manager(db: AsyncSession = Depends(get_db)) -> AgentManager:
    """Get agent manager service."""
    return AgentManager(db=db)

def get_chat_manager(db: AsyncSession = Depends(get_db)) -> ChatManager:
    """Get chat manager service."""
    return ChatManager(db=db) 