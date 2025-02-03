import hashlib
import logging
from dataclasses import dataclass
from typing import Dict, Any, Union, Optional

from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_chroma import Chroma

from app.config import settings
from app.dependencies import get_embedding_function
from app.utils.text_loader import RawTextLoader
from app.models.database import Agent
from sqlalchemy.orm import Session

from app.services.base import BaseAgentService
from app.services.document.processor import DocumentProcessor
from app.services.document.loader import DocumentLoader
from app.services.document.factory import LoaderFactory

logger = logging.getLogger(__name__)

LoaderType = Union[WebBaseLoader, PyPDFLoader, RawTextLoader]

@dataclass
class DocumentMetadata:
    """Metadata container for indexed documents.
    
    Attributes:
        document_hash: SHA-256 hash of the source content
        chunk_count: Number of generated text chunks
        source_type: Type of source (web, pdf, text)
        additional_metadata: Custom metadata from processing
    """
    document_hash: str
    chunk_count: int
    source_type: str
    additional_metadata: Dict[str, Any]

class IndexingService(BaseAgentService):
    """Orchestrates document ingestion and indexing workflow.
    
    Handles the complete pipeline from document loading to storage in:
    1. Vector database (Chroma)
    2. Relational database (PostgreSQL)
    
    Uses strategy pattern for different document types via LoaderFactory.
    """

    def __init__(self, agent_id: str, db: Session):
        """
        Args:
            agent_id: UUID of the agent owning the documents
            db: Active database session
        """
        super().__init__(agent_id, db)
        self.document_processor = DocumentProcessor()
        self.document_loader = DocumentLoader()
        self.vector_store = self._initialize_vector_store()
    
    @staticmethod
    def _compute_document_hash(source: str) -> str:
        """Generate unique fingerprint for document content.
        
        Args:
            source: Raw document content or file path
            
        Returns:
            SHA-256 hex digest of the content
        """
        return hashlib.sha256(source.encode()).hexdigest()

    async def index_content(
        self,
        source: str,
        source_type: str = "web",
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentMetadata:
        """Main entry point for document ingestion pipeline.
        
        1. Computes document hash
        2. Loads and processes documents
        3. Stores in both vector and relational DBs
        
        Args:
            source: Content source (URL, file path, or raw text)
            source_type: One of 'web', 'pdf', or 'text'
            metadata: Custom metadata for document tracking
            
        Returns:
            Processed document metadata with system-generated fields
            
        Raises:
            Exception: Any failure in the ingestion pipeline
        """
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
        """Execute document loading and processing steps.
        
        1. Factory creates source-specific loader
        2. Loader fetches/parses content
        3. Processor splits and enriches documents
        
        Args:
            source: Content location or raw text
            source_type: Determines loader strategy
            
        Returns:
            List of processed document chunks with metadata
        """
        loader = LoaderFactory.create_loader(source, source_type)
        documents = await self.document_loader.load_documents(loader)
        self.document_loader.validate_documents(documents)
        
        return await self.document_processor.process_documents(
            documents,
            {"source": source, "source_type": source_type}
        )

    async def _store_documents(self, documents, metadata):
        """Persist documents to storage systems.
        
        Dual-write to:
        1. Chroma vector store for retrieval
        2. PostgreSQL for metadata tracking
        
        Args:
            documents: Processed document chunks
            metadata: System-generated document metadata
            
        Raises:
            Exception: Rollback on any storage failure
        """
        try:
            # Vector store insertion
            self.vector_store.add_documents(documents)
            
        except Exception as e:
            logger.error(f"Storage failed: {str(e)}")
            raise