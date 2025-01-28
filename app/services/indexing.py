
import logging
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, TextLoader
from langchain_chroma import Chroma
from app.config import settings

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)

class IndexingService:
    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.embedding_model, device=settings.device)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.vector_store = Chroma(
            persist_directory=settings.chroma_db_path,
            embedding_function=self.embedding_model.encode
        )

    async def index_content(self, source: str, source_type: str = "web"):
        try:
            loader = self._get_loader(source, source_type)
            documents = loader.load()
            splits = self.text_splitter.split_documents(documents)
            self.vector_store.add_documents(splits)
            return True
        except Exception as e:
            logger.error(f"Indexing error: {str(e)}")
            raise

    def _get_loader(self, source: str, source_type: str):
        if source_type == "web":
            return WebBaseLoader(source)
        elif source_type == "pdf":
            return PyPDFLoader(source)
        elif source_type == "text":
            return TextLoader(source)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")