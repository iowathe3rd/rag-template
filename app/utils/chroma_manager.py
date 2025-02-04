from app.core.config import settings
from chromadb import HttpClient

_chroma_client = None

def get_chroma_client():
    """Return a cached Chroma client instance."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = HttpClient(
            host=settings.chroma.host,
            port=settings.chroma.port,
        )

    
    _chroma_client.list_collections()

    return _chroma_client