from app.services.base import BaseAgentService
from app.models.chat import ChatManager
from app.models.rag import RAGChainManager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

@dataclass
class RetrievalResponse:
    """Data class for storing retrieval results."""
    answer: str
    sources: List[str]
    metadata: Dict[str, Any]
    confidence_score: float

class RetrievalService(BaseAgentService):
    """Service for retrieving and generating answers using RAG pattern."""

    def __init__(self, agent_id: str, db: Session):
        super().__init__(agent_id, db)
        self.chat_manager = ChatManager(db)
        self.rag_chain = RAGChainManager(
            vector_store=self.vector_store,
            model_name=self.agent.llm_config["model_name"],
            retrieval_config=self.agent.rag_config
        )
    async def get_answer(self, question: str, chat_id: Optional[str] = None) -> RetrievalResponse:
        context = await self._get_context(question, chat_id)
        response = await self.rag_chain.generate_response(context)
        
        if chat_id:
            await self._save_interaction(chat_id, question, response)
        
        return response

    async def _get_context(self, question: str, chat_id: Optional[str]) -> str:
        if not chat_id:
            return question
        
        chat_history = await self.chat_manager.get_chat_history(
            self.agent_id, 
            chat_id
        )
        return f"{chat_history}\n{question}"