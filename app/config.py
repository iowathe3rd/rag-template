from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_name: str = "deepseek-ai/deepseek-v3"  # Или другая open-source модель
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_db_path: str = "./chroma_db"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    device: str = "cpu"  # Используйте "cpu", если нет GPU
    api_key: str

    class Config:
        env_file = ".env"

settings = Settings()