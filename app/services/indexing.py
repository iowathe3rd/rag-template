import logging
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, TextLoader
from langchain_chroma import Chroma
from app.config import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.ollama_embed import OllamaEmbedding
from typing import List, Dict, Any
from langchain_core.documents import Document
import hashlib
from app.utils.text_loader import RawTextLoader

logger = logging.getLogger(__name__)

class IndexingService:
    def __init__(self, vector_store: Chroma):
        if not settings.is_valid_chunk_config:
            raise ValueError("Invalid chunk configuration")
            
        self.vector_store = vector_store
        self.embedding_function = OllamaEmbedding()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )

    async def index_content(self, source: str, source_type: str = "web", metadata: Dict[str, Any] = None) -> bool:
        try:
            document_hash = self._compute_document_hash(source)
            if await self._is_document_indexed(document_hash):
                logger.info(f"Document already indexed: {source}")
                return False

            loader = self._get_loader(source, source_type)
            if source_type == "web":
                documents = loader.scrape()  # Removed 'await'
            else:
                documents: list[Document] = await self._load_and_validate_documents(loader)
            splits = self.text_splitter.split_documents(documents)
            
            # Add document hash to metadata
            for split in splits:
                split.metadata.update({
                    "document_hash": document_hash,
                    **(metadata or {})
                })

            self.vector_store.add_documents(splits)
            return True
            
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            raise

    @staticmethod
    def _compute_document_hash(source: str) -> str:
        return hashlib.sha256(source.encode()).hexdigest()

    async def _is_document_indexed(self, document_hash: str) -> bool:
        # Implement document deduplication logic
        return False  # Placeholder implementation

    async def _load_and_validate_documents(self, loader: Any) -> List[Document]:
        """Load and validate documents from the loader."""
        try:
            if isinstance(loader, RawTextLoader):
                documents = loader.load()
            else:
                documents = await loader.aload() if hasattr(loader, 'aload') else loader.load()
            
            if not documents:
                raise ValueError("No documents loaded")
            return documents
        except Exception as e:
            logger.error(f"Document loading failed: {str(e)}")
            raise

    def _get_loader(self, source: str, source_type: str) -> WebBaseLoader | PyPDFLoader | TextLoader:
        """Get appropriate loader based on source type."""
        if source_type == "web":
            return WebBaseLoader(source)
        elif source_type == "pdf":
            return PyPDFLoader(source)
        elif source_type == "text":
            return RawTextLoader(source)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")