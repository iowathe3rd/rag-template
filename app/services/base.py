from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from langchain_chroma import Chroma
from app.models.database import Agent, chroma_manager
from app.dependencies import get_embedding_function

class BaseAgentService(ABC):
    """
    Abstract base class for agent services.
    """
    def __init__(self, agent_id: str, db: Session):
        """
        Initialize the base agent service.
        """
        self.agent_id: str = agent_id
        self.db: Session = db
        self._vector_store: Optional[Chroma] = None
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        """
        Get the agent.
        """
        if not self._agent:
            self._agent = self._get_agent()
        return self._agent

    @property
    def vector_store(self) -> Chroma:
        """
        Get the vector store.
        """
        if not self._vector_store:
            self._vector_store = self._initialize_vector_store()
        return self._vector_store

    def _get_agent(self) -> Agent:
        """
        Get the agent from the database.
        """
        agent = self.db.query(Agent).filter(Agent.id == self.agent_id).first()
        if not agent:
            raise ValueError(f"Agent {self.agent_id} not found")
        return agent

    def _initialize_vector_store(self) -> Chroma:
        """
        Initialize the vector store.
        """
        collection = chroma_manager.get_or_create_collection(
            name=str(self.agent_id),  # Используем UUID агента как название
            metadata={"hnsw:space": "cosine"}
        )
        return Chroma(
            client=chroma_manager.client,
            collection_name=collection.name,
            embedding_function=get_embedding_function()
        )