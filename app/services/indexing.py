import hashlib
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Union, AsyncIterator
from pathlib import Path

from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.utils.ollama_embed import OllamaEmbedding
from app.utils.text_loader import RawTextLoader

logger = logging.getLogger(__name__)

LoaderType = Union[WebBaseLoader, PyPDFLoader, RawTextLoader]

@dataclass
class DocumentMetadata:
    document_hash: str
    additional_metadata: Dict[str, Any]

class DocumentProcessor:
    """Handles document loading and validation operations."""
    
    @staticmethod
    async def load_documents(loader: LoaderType) -> List[Document]:
        """Load documents based on loader type."""
        if isinstance(loader, PyPDFLoader):
            return [doc async for doc in loader.alazy_load()]
        if isinstance(loader, RawTextLoader):
            return loader.load()
        return loader.load()

    @staticmethod
    def validate_documents(documents: List[Document]) -> None:
        """Validate document structure and content."""
        if not documents:
            raise ValueError("No documents were loaded from the source")
        
        for doc in documents:
            if not isinstance(doc, Document):
                raise TypeError(f"Invalid document type: {type(doc)}")
            if not doc.page_content:
                logger.warning("Document found with empty content")

class LoaderFactory:
    """Factory for creating document loaders."""
    
    @staticmethod
    def create_loader(source: str, source_type: str) -> LoaderType:
        """Create appropriate loader based on source type."""
        loaders = {
            "web": lambda s: WebBaseLoader(s),
            "pdf": lambda s: PyPDFLoader(s, extract_images=False),
            "text": lambda s: RawTextLoader(s)
        }
        
        if source_type not in loaders:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        return loaders[source_type](source)

class IndexingService:
    """Service for indexing documents into vector store."""

    def __init__(self, vector_store: Chroma):
        if not settings.is_valid_chunk_config:
            raise ValueError("Invalid chunk configuration")
            
        self.vector_store = vector_store
        self.text_splitter = self._create_text_splitter()
        self.document_processor = DocumentProcessor()
        self.loader_factory = LoaderFactory()

    @staticmethod
    def _create_text_splitter() -> RecursiveCharacterTextSplitter:
        """Create text splitter with configured settings."""
        return RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )

    @staticmethod
    def _compute_document_hash(source: str) -> str:
        """Compute SHA-256 hash of the source."""
        return hashlib.sha256(source.encode()).hexdigest()

    def _prepare_document_metadata(self, source: str, metadata: Dict[str, Any] = None) -> DocumentMetadata:
        """Prepare metadata for documents."""
        return DocumentMetadata(
            document_hash=self._compute_document_hash(source),
            additional_metadata=metadata or {}
        )

    async def index_content(self, source: str, source_type: str = "web", metadata: Dict[str, Any] = None) -> bool:
        """Index content from various sources into the vector store."""
        try:
            doc_metadata = self._prepare_document_metadata(source, metadata)
            loader = self.loader_factory.create_loader(source, source_type)
            
            # Load and process documents
            documents = await self.document_processor.load_documents(loader)
            self.document_processor.validate_documents(documents)
            
            # Handle web content specifically
            if source_type == "web":
                documents = [Document(page_content=str(item)) for item in documents]
            
            # Split and update metadata
            splits = self.text_splitter.split_documents(documents)
            for split in splits:
                split.metadata.update({
                    "document_hash": doc_metadata.document_hash,
                    **doc_metadata.additional_metadata
                })

            self.vector_store.add_documents(splits)
            return True
            
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            raise