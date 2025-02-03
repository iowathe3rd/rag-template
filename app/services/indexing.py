import hashlib
import logging
from dataclasses import dataclass
from typing import Dict, Any, Union, Optional

from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_chroma import Chroma

from app.config import settings
from app.dependencies import get_embedding_function
from app.utils.text_loader import RawTextLoader
from app.models.database import Agent, DocumentChunk
from sqlalchemy.orm import Session

from app.services.base import BaseAgentService
from app.services.document.processor import DocumentProcessor
from app.services.document.loader import DocumentLoader
from app.services.document.factory import LoaderFactory

logger = logging.getLogger(__name__)

LoaderType = Union[WebBaseLoader, PyPDFLoader, RawTextLoader]

@dataclass
class DocumentMetadata:
    document_hash: str
    chunk_count: int
    source_type: str
    additional_metadata: Dict[str, Any]

class IndexingService(BaseAgentService):
    """Service for indexing documents into agent-specific vector store."""

    def __init__(self, agent_id: str, db: Session):
        super().__init__(agent_id, db)
        self.document_processor = DocumentProcessor()
        self.document_loader = DocumentLoader()
        self.vector_store = self._get_agent_vector_store()

    def _get_agent_vector_store(self) -> Chroma:
        """Get or create agent-specific vector store."""
        agent = self.db.query(Agent).filter(Agent.id == self.agent_id).first()
        if not agent:
            raise ValueError(f"Agent {self.agent_id} not found")

        # Create or get agent-specific Chroma collection
        return Chroma(
            collection_name=agent.chroma_collection_name,
            embedding_function=get_embedding_function(),
        )

    @staticmethod
    def _compute_document_hash(source: str) -> str:
        """Compute SHA-256 hash of the source."""
        return hashlib.sha256(source.encode()).hexdigest()

    async def index_content(
        self,
        source: str,
        source_type: str = "web",
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentMetadata:
        """Index content from various sources."""
        try:
            metadata = metadata or {}
            metadata["agent_id"] = self.agent_id
            metadata["document_hash"] = self._compute_document_hash(source)
            
            documents = await self._load_and_process_documents(source, source_type)
            await self._store_documents(documents, metadata)
            
            return DocumentMetadata(
                document_hash=metadata["document_hash"],
                chunk_count=len(documents),
                source_type=source_type,
                additional_metadata=metadata
            )
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            raise

    async def _load_and_process_documents(self, source: str, source_type: str):
        """Load and process documents."""
        loader = LoaderFactory.create_loader(source, source_type)
        documents = await self.document_loader.load_documents(loader)
        self.document_loader.validate_documents(documents)
        
        return await self.document_processor.process_documents(
            documents,
            {"source": source, "source_type": source_type}
        )

    async def _store_documents(self, documents, metadata):
        """Store documents in vector store and database."""
        try:
            self.vector_store.add_documents(documents)
            
            for doc in documents:
                chunk = DocumentChunk(
                    agent_id=self.agent_id,
                    content=doc.page_content,
                    vector=doc.embedding,
                    metadata=metadata,
                    document_hash=metadata["document_hash"]
                )
                self.db.add(chunk)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Storage failed: {str(e)}")
            raise