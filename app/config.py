import chromadb
from pydantic_settings import BaseSettings
import chromadb.utils.embedding_functions as embedding_functions
from typing import Optional, List

class Settings(BaseSettings):
    # Model settings
    model_name: str = "together_ai/deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
    embedding_model: str = "togethercomputer/m2-bert-80M-8k-retrieval"
    
    # Database settings
    chroma_db_path: str = "/app/data/chroma_db"
    chroma_collection_name: str = "documents"
    
    # LangSmith settings
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str = ""
    langsmith_project: str = "rag-assistant"
    
    #together ai settings
    togetherai_api_key: str = ""
    
    # Text splitting settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Hardware settings
    device: str = "cpu"
    
    # Retrieval settings
    similarity_top_k: int = 3
    similarity_score_threshold: Optional[float] = None  # Remove threshold for now
    score_normalization: bool = True
    
    # Ingestion settings
    allowed_extensions: List[str] = ["pdf", "txt"]
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    temp_file_path: str = "/app/data/temp"
    
    # Generation settings
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 1.0

    @property
    def is_valid_chunk_config(self) -> bool:
        return 0 < self.chunk_overlap < self.chunk_size

    class Config:
        env_file = ".env"

settings = Settings()