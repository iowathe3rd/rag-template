from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, Field
from typing import Optional, List

class ChromaDBSettings(BaseSettings):
    host: str = Field(..., env="CHROMA_HOST")
    port: int = Field(8000, env="CHROMA_PORT")
    auth_provider: str = Field(..., env="CHROMA_AUTH_PROVIDER")
    auth_credentials: str = Field(..., env="CHROMA_AUTH_CREDENTIALS")
    persist_dir: str = Field(..., env="CHROMA_PERSIST_DIR")

class PostgresSettings(BaseSettings):
    host: str = Field(..., env="POSTGRES_HOST")
    port: int = Field(5432, env="POSTGRES_PORT")
    user: str = Field(..., env="POSTGRES_USER")
    password: str = Field(..., env="POSTGRES_PASSWORD")
    db: str = Field(..., env="POSTGRES_DB")
    
    @property
    def dsn(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=str(self.port),
            path=self.db,
        )

class Settings(BaseSettings):
    postgres: PostgresSettings = PostgresSettings()
    chroma: ChromaDBSettings = ChromaDBSettings()
    
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

    @property
    def chroma_client_settings(self) -> dict:
        return {
            "chroma_server_host": self.chroma.host,
            "chroma_server_port": self.chroma.port,
            "chroma_server_ssl": False,
            "chroma_client_auth_provider": self.chroma.auth_provider,
            "chroma_client_auth_credentials": self.chroma.auth_credentials
        }

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False

settings = Settings()