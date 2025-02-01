from dataclasses import dataclass
from langchain import hub
from langchain_chroma import Chroma
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableParallel,
    Runnable,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
import logging
import litellm
from typing import Any, Dict, List, Optional, Union
from langchain_core.vectorstores import VectorStoreRetriever
from sqlalchemy.orm import Session
from app.models.database import Chat as DBChat
import json

logger = logging.getLogger(__name__)

@dataclass
class RetrievalResponse:
    """Data class for storing retrieval results."""
    answer: str
    sources: List[str]
    metadata: Dict[str, Any]

class RetrievalService:
    """Service for retrieving and generating answers using RAG pattern."""

    def __init__(self, vector_store: Chroma) -> None:
        """
        Initialize the retrieval service.
        
        Args:
            vector_store: Initialized Chroma vector store
        """
        self._validate_vector_store(vector_store)
        self.vector_store = vector_store
        self.device = settings.device
        self.model = settings.model_name
        self.retriever = self._setup_retriever()
        self.prompt: ChatPromptTemplate = hub.pull("rlm/rag-prompt")
        self.setup_chain()

    @staticmethod
    def _validate_vector_store(vector_store: Chroma) -> None:
        """Validate that vector store contains documents."""
        if not vector_store._collection.count():
            logger.warning("Vector store is empty")

    def _setup_retriever(self) -> VectorStoreRetriever:
        """
        Configure the retriever with search settings.
        
        Returns:
            Configured retriever instance
        """
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.similarity_top_k}
        )

    def setup_chain(self) -> None:
        """Initialize the RAG processing chain."""
        self.rag_chain = (
            RunnableParallel({
                "context": self.retriever,
                "question": RunnablePassthrough()
            })
            | self.prompt
            | self._extract_content
            | self._generate_answer
            | StrOutputParser()
        )

    @staticmethod
    def _extract_content(x: Any) -> str:
        """Extract content from prompt response."""
        return x.content if hasattr(x, 'content') else str(x)

    async def get_answer(self, context: str) -> RetrievalResponse:
        """
        Get answer and sources for the given context.
        
        Args:
            context: Combined chat history and user question
            
        Returns:
            RetrievalResponse containing answer, sources and metadata
            
        Raises:
            ValueError: If empty context provided
        """
        if not context.strip():
            raise ValueError("Empty context provided")
        
        try:
            answer = await self.rag_chain.ainvoke(context)
            sources = await self._get_sources(context)
            
            if not sources:
                logger.warning("No sources found for the answer")
            
            return RetrievalResponse(
                answer=answer or "I couldn't find relevant information to answer your question.",
                sources=sources,
                metadata={
                    "model": settings.model_name,
                    "source_count": len(sources)
                }
            )
        except Exception as e:
            logger.error(f"Retrieval pipeline failed: {str(e)}")
            raise

    async def _generate_answer(self, prompt: Union[str, BaseMessage]) -> str:
        """
        Generate answer using LLM.
        
        Args:
            prompt: Input prompt for the LLM
            
        Returns:
            Generated answer string
        """
        try:
            prompt_text = prompt.content if isinstance(prompt, BaseMessage) else str(prompt)
            response = await self._call_llm(prompt_text)
            return response['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Generation error: {str(e)}, prompt: {prompt}")
            raise

    async def _call_llm(self, prompt_text: str) -> Dict[str, Any]:
        """Make the actual LLM API call."""
        return await litellm.acompletion(
            model=self.model,
            messages=[{"role": "user", "content": prompt_text}],
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            top_p=settings.top_p
        )

    async def _get_sources(self, question: str) -> List[str]:
        """
        Get list of unique sources for the answer.
        
        Args:
            question: User question string
            
        Returns:
            List of unique source strings
        """
        try:
            docs = self.retriever.get_relevant_documents(question)
            if not docs:
                logger.warning("No documents retrieved")
                return []
                
            return list({
                doc.metadata.get("source", "") 
                for doc in docs 
                if hasattr(doc, "metadata")
            })
        except Exception as e:
            logger.error(f"Source retrieval error: {str(e)}")
            return []

    async def save_chat_message(self, agent_id: str, chat_id: str, message: str, db: Session):
        db_chat = db.query(DBChat).filter(DBChat.id == chat_id, DBChat.agent_id == agent_id).first()
        if not db_chat:
            raise ValueError("Chat not found")
        
        db_chat.add_message(message)
        db.commit()

    async def get_chat_history(self, agent_id: str, chat_id: str, db: Session) -> List[str]:
        db_chat = db.query(DBChat).filter(DBChat.id == chat_id, DBChat.agent_id == agent_id).first()
        if not db_chat:
            raise ValueError("Chat not found")
        return json.loads(db_chat.messages)