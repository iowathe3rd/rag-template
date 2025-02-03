from typing import List, Union
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_core.documents import Document
from app.utils.text_loader import RawTextLoader
import logging

logger = logging.getLogger(__name__)

LoaderType = Union[WebBaseLoader, PyPDFLoader, RawTextLoader]

class DocumentLoader:
    """Handles document loading operations."""
    
    @staticmethod
    async def load_documents(loader: LoaderType) -> List[Document]:
        """Load documents based on loader type."""
        try:
            if isinstance(loader, PyPDFLoader):
                return [doc async for doc in loader.alazy_load()]
            if isinstance(loader, RawTextLoader):
                return loader.load()
            return loader.load()
        except Exception as e:
            logger.error(f"Document loading failed: {str(e)}")
            raise

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