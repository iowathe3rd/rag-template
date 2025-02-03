from pydantic_settings import BaseSettings
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
    
    # Vector store cache settings
    VECTOR_STORE_CACHE_SIZE: int = 100  # Maximum number of cached vector stores
    EMBEDDING_CACHE_TTL: int = 3600  # Time to live for cached embeddings in seconds
    
    # Database connection settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    
    # ChromaDB settings
    chroma_host: str = "chroma"
    chroma_port: int = 8001
    chroma_auth_credentials: str = "admin:admin"
    
    # PostgreSQL settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "rag_db"

    @property
    def is_valid_chunk_config(self) -> bool:
        return 0 < self.chunk_overlap < self.chunk_size

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_file = ".env"

settings = Settings()