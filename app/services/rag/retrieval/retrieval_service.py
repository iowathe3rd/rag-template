from app.services.rag.base import BaseAgentService
from app.services.chat.manager import ChatManager
from app.services.rag.chain import RAGChainManager
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.retrieveal import RetrievalResponse
from app.schemas.chat import ChatMessage as ChatMessageSchema


class RetrievalService(BaseAgentService):
    """Orchestrates question answering using RAG pattern.
    
    Combines:
    1. Vector store retrieval
    2. LLM generation
    3. Conversation history management
    """

    def __init__(self, agent_id: str, db: AsyncSession):
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

    async def _save_interaction(self, chat_id: str, question: str, response: RetrievalResponse):
        """Persist interaction to chat history"""
        await self.chat_manager.add_message_to_chat(
            chat_id,
            ChatMessageSchema(role="user", content=question)
        )
        await self.chat_manager.add_message_to_chat(
            chat_id,
            ChatMessageSchema(role="assistant", content=response.answer)
        ) 