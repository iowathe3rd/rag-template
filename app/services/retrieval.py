from app.dependencies import get_embedding_function
from app.services.base import BaseAgentService
from app.models.chat import ChatManager
from app.models.rag import RAGChainManager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from langchain.vectorstores import Chroma
from langchain.vectorstores.base import VectorStore
from app.models.database import chroma_manager

@dataclass
class RetrievalResponse:
    """Container for RAG system response components.
    
    Attributes:
        answer: Generated answer text
        sources: Source documents used for generation
        metadata: System metadata about the retrieval
        confidence_score: Confidence metric (0-1)
    """
    answer: str
    sources: List[str]
    metadata: Dict[str, Any]
    confidence_score: float

class RetrievalService(BaseAgentService):
    """Orchestrates question answering using RAG pattern.
    
    Combines:
    1. Vector store retrieval
    2. LLM generation
    3. Conversation history management
    """

    def __init__(self, agent_id: str, db: Session):
        """
        Args:
            agent_id: UUID of the agent to query
            db: Active database session
        """
        super().__init__(agent_id, db)
        self.chat_manager = ChatManager(db)
        self.rag_chain = RAGChainManager(
            vector_store=self.vector_store,
        )

    async def get_answer(self, question: str, chat_id: Optional[str] = None) -> RetrievalResponse:
        """Main entry point for question answering.
        
        1. Augments question with chat history
        2. Executes RAG pipeline
        3. Persists conversation context
        
        Args:
            question: User's natural language query
            chat_id: Optional conversation ID for history
            
        Returns:
            Structured RAG system response
            
        Raises:
            Exception: Propagation from RAG chain failures
        """
        context = await self._get_context(question, chat_id)
        response = await self.rag_chain.generate_response(context)
        
        if chat_id:
            await self._save_interaction(chat_id, question, response)
        
        return response

    async def _get_context(self, question: str, chat_id: Optional[str]) -> str:
        """Builds contextual prompt from conversation history.
        
        Args:
            question: Current user question
            chat_id: Lookup key for historical messages
            
        Returns:
            Question augmented with relevant chat history
        """
        if not chat_id:
            return question
        
        chat_history = await self.chat_manager.get_chat_history(
            self.agent_id, 
            chat_id
        )
        return f"{chat_history}\n{question}"

    def _init_vector_store(self) -> VectorStore:
        """Инициализация хранилища векторов для конкретного агента"""
        return Chroma(
            client=chroma_manager.client,
            collection_name=str(self.agent_id),  # Используем UUID агента
            embedding_function=get_embedding_function(),
        )