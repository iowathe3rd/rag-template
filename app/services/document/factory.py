from typing import Dict, Callable
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from app.utils.text_loader import RawTextLoader
from .loader import LoaderType

class LoaderFactory:
    """Factory for creating document loaders."""
    
    _loaders: Dict[str, Callable[[str], LoaderType]] = {
        "web": lambda s: WebBaseLoader(s),
        "pdf": lambda s: PyPDFLoader(s, extract_images=False),
        "text": lambda s: RawTextLoader(s)
    }
    
    @classmethod
    def create_loader(cls, source: str, source_type: str) -> LoaderType:
        """Create appropriate loader based on source type."""
        if source_type not in cls._loaders:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        return cls._loaders[source_type](source) 