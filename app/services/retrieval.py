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

# Initialize logger
logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self, vector_store: Chroma):
        self._validate_vector_store(vector_store)
        self.device = settings.device
        self.model = settings.model_name
        self.vector_store = vector_store
        self.retriever = self._setup_retriever()
        self.prompt: ChatPromptTemplate = hub.pull("rlm/rag-prompt")
        self.rag_chain: Runnable
        self.setup_chain()

    @staticmethod
    def _validate_vector_store(vector_store: Chroma) -> None:
        if not vector_store._collection.count():
            logger.warning("Vector store is empty")

    def _setup_retriever(self):
        """Configure the retriever with proper settings."""
        return self.vector_store.as_retriever(
            search_type="similarity",  # Changed from similarity_score_threshold
            search_kwargs={
                "k": settings.similarity_top_k,
            }
        )

    def setup_chain(self) -> None:
        """Initialize RAG processing chain."""
        self.rag_chain = (
            RunnableParallel(
                {
                    "context": self.retriever, 
                    "question": RunnablePassthrough()
                }
            )
            | self.prompt
            | (lambda x: x.content if hasattr(x, 'content') else str(x))  # Extract content from prompt
            | self._generate_answer
            | StrOutputParser()
        )

    async def get_answer(self, question: str) -> Dict[str, Any]:
        """Get answer and sources for the given question."""
        if not question.strip():
            raise ValueError("Empty question provided")
        
        try:
            answer = await self.rag_chain.ainvoke(question)
            sources = await self._get_sources(question)
            
            if not sources:
                logger.warning("No sources found for the answer")
            
            return {
                "answer": answer or "I couldn't find relevant information to answer your question.",
                "sources": sources,
                "metadata": {
                    "model": settings.model_name,
                    "source_count": len(sources)
                }
            }
        except Exception as e:
            logger.error(f"Retrieval pipeline failed: {str(e)}")
            raise

    async def _generate_answer(self, prompt: Union[str, BaseMessage]) -> str:
        """Generate answer using LLM."""
        try:
            # Convert prompt to string if it's a BaseMessage
            if isinstance(prompt, BaseMessage):
                prompt_text = prompt.content
            else:
                prompt_text = str(prompt)

            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt_text}],
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                top_p=settings.top_p
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Generation error: {str(e)}, prompt: {prompt}")
            raise

    def _normalize_score(self, score: float) -> float:
        """Normalize negative scores to 0-1 range."""
        return 1 / (1 + abs(score)) if score < 0 else score

    async def _get_sources(self, question: str) -> List[str]:
        """Get list of unique sources for the answer."""
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