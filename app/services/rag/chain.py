import datetime
from typing import Any, Dict, List
from fastapi import logger
from langchain import hub
from langchain_chroma import Chroma
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.vectorstores import VectorStoreRetriever
from litellm import LiteLLM
from app.core.config import settings
from app.schemas.retrieveal import RetrievalResponse

class RAGChainManager:
    """Manages RAG (Retrieval Augmented Generation) chain operations."""
    
    def __init__(
        self, 
        vector_store: Chroma,
    ):
        """
        Initialize RAG chain manager.
        
        Args:
            vector_store: Chroma vector store instance
            model_name: Name of the LLM model to use
        """
        self.vector_store = vector_store
        self.model_name = settings.model_name
        self.retriever = self._setup_retriever()
        self.llm = self._setup_llm()
        self.prompt = hub.pull("rlm/rag-prompt")
        self.chain = self._setup_chain()

    def _setup_llm(self) -> LiteLLM:
        """Initialize the LLM with configuration."""
        return LiteLLM(
            model_name=settings.model_name,
            api_key=settings.togetherai_api_key,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            top_p=settings.top_p
        )

    def _setup_retriever(self) -> VectorStoreRetriever:
        """Initialize the retriever with search configuration."""
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": settings.similarity_top_k,
                "score_threshold": settings.similarity_score_threshold
            }
        )

    def _setup_chain(self):
        """Initialize the RAG chain with parallel retrieval and processing."""
        return (
            RunnableParallel({
                "context": self.retriever,
                "question": RunnablePassthrough()
            })
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    async def _get_sources(self, question: str) -> List[str]:
        """Retrieve source documents for a given question."""
        docs = await self.retriever.aget_relevant_documents(question)
        return [doc.page_content for doc in docs]

    def _calculate_confidence(self, answer: str, sources: List[str]) -> float:
        """Calculate confidence score for the generated answer."""
        if not sources:
            return 0.0  # No sources, low confidence

        # Simple heuristic: more sources = higher confidence
        # You can add more sophisticated logic here, like semantic similarity
        # between the answer and the sources, or using LLM's confidence if available
        
        num_sources = len(sources)
        max_sources = settings.similarity_top_k # Assuming max sources is the k value
        
        # Normalize the number of sources to a 0-1 range
        source_confidence = min(1.0, num_sources / max_sources)
        
        # Placeholder for more advanced confidence calculation
        # For example, you could use an embedding model to compare the answer
        # to the sources and calculate a similarity score.
        
        # Combine source confidence with a base confidence
        base_confidence = 0.5 # You can adjust this
        confidence = base_confidence + (source_confidence * (1 - base_confidence))
        
        return confidence

    def _get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the RAG operation."""
        return {
            "model": self.model_name,
            "retrieval_config": {
                "k": settings.similarity_top_k,
                "score_threshold": settings.similarity_score_threshold
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    async def generate_response(self, question: str) -> RetrievalResponse:
        """
        Generate a response using the RAG chain.
        
        Args:
            question: User's question
            
        Returns:
            RetrievalResponse containing answer, sources, and metadata
        """
        try:
            answer = await self.chain.ainvoke(question)
            sources = await self._get_sources(question)
            
            return RetrievalResponse(
                answer=answer,
                sources=sources,
                metadata=self._get_metadata(),
                confidence_score=self._calculate_confidence(answer, sources)
            )
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            raise ValueError(f"Failed to generate response: {str(e)}")