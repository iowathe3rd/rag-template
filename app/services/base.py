from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from langchain_chroma import Chroma
from app.models.database import Agent, chroma_manager
from app.dependencies import get_embedding_function

class BaseAgentService(ABC):
    def __init__(self, agent_id: str, db: Session):
        self.agent_id: str = agent_id
        self.db: Session = db
        self._vector_store: Optional[Chroma] = None
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        if not self._agent:
            self._agent = self._get_agent()
        return self._agent

    @property
    def vector_store(self) -> Chroma:
        if not self._vector_store:
            self._vector_store = self._initialize_vector_store()
        return self._vector_store

    def _get_agent(self) -> Agent:
        agent = self.db.query(Agent).filter(Agent.id == self.agent_id).first()
        if not agent:
            raise ValueError(f"Agent {self.agent_id} not found")
        return agent

    def _initialize_vector_store(self) -> Chroma:
        collection = chroma_manager.get_or_create_collection(
            f"agent_{self.agent_id}"
        )
        return Chroma(
            client=chroma_manager.client,
            collection_name=collection.name,
            embedding_function=get_embedding_function()
        )