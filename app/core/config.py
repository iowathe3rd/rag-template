from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pydantic import BaseModel

class ChromaAuth(BaseModel):
    provider: str
    credentials: str
    header: str

class Chroma(BaseModel):
    host: str
    port: int
    auth: ChromaAuth

class Postgres(BaseModel):
    host: str
    port: int
    user: str
    password: str
    db: str
    
    @property
    def dsn(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
    
class Settings(BaseSettings):
    postgres: Postgres
    chroma: Chroma
    
    # Model settings
    model_name: str = "together_ai/deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
    embedding_model: str = "togethercomputer/m2-bert-80M-8k-retrieval"
    # LangSmith settings
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str = ""
    langsmith_project: str = "rag-assistant"
    
    # together ai settings
    togetherai_api_key: str = ""
    
    # Text splitting settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

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
    
    @property
    def database_url(self):
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter='_')

settings = Settings()