from chromadb import Documents, EmbeddingFunction, Embeddings
from app.config import settings
import ollama
import logging
from typing import List, Union
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class OllamaEmbedding(EmbeddingFunction):
    def __init__(self):
        self.client = ollama.Client()
        self.model_name = settings.embedding_model
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        try:
            response = self.client.embeddings(model=self.model_name, prompt=text)
            if not response or 'embedding' not in response:
                raise ValueError("No embedding in response")
            return response['embedding']
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise

    def embed_documents(self, texts: Documents) -> Embeddings:
        """Generate embeddings for documents."""
        embeddings = []
        for text in texts:
            try:
                if not isinstance(text, str):
                    raise ValueError(f"Invalid input type: {type(text)}")
                embedding = self._get_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Document embedding failed: {str(e)}")
                embeddings.append(None)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for query text."""
        return self._get_embedding(text)

    def __call__(self, texts: Union[str, Documents]) -> Union[List[float], Embeddings]:
        """Handle both single text and document list inputs."""
        if isinstance(texts, str):
            return self.embed_query(texts)
        return self.embed_documents(texts)