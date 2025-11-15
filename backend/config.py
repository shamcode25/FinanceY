"""
Configuration settings for FinanceY
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # OpenAI Configuration
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (required for LLM features)"
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use"
    )
    openai_temperature: float = Field(
        default=0.0,
        description="Temperature for OpenAI API calls"
    )
    openai_max_tokens: int = Field(
        default=2000,
        description="Maximum tokens for OpenAI responses"
    )
    
    # RAG Configuration
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model"
    )
    embedding_dimension: int = Field(
        default=1536,
        description="Dimension of embeddings"
    )
    chunk_size: int = Field(
        default=1000,
        description="Text chunk size for RAG"
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks"
    )
    top_k_retrieval: int = Field(
        default=5,
        description="Number of chunks to retrieve for RAG"
    )
    
    # Paths
    data_dir: str = Field(
        default="./data",
        description="Base data directory"
    )
    filings_dir: str = Field(
        default="./data/filings",
        description="Directory for SEC filings"
    )
    vector_db_path: str = Field(
        default="./data/vectorstore",
        description="Path to FAISS vector database"
    )
    transcripts_dir: str = Field(
        default="./data/transcripts",
        description="Directory for earnings transcripts"
    )
    news_dir: str = Field(
        default="./data/news",
        description="Directory for news articles"
    )
    
    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API host"
    )
    api_port: int = Field(
        default=8000,
        description="API port"
    )
    api_reload: bool = Field(
        default=True,
        description="Enable auto-reload in development"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key is provided"""
        if not v or v == "your_openai_api_key_here":
            import warnings
            warnings.warn("OPENAI_API_KEY not set. LLM features will not work. Please set it in .env file.")
            return ""  # Return empty string instead of raising error
        return v
    
    @field_validator("data_dir", "filings_dir", "vector_db_path", "transcripts_dir", "news_dir")
    @classmethod
    def validate_paths(cls, v: str) -> str:
        """Ensure paths are absolute and create directories if needed"""
        path = Path(v).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    def get_filings_path(self) -> Path:
        """Get Path object for filings directory"""
        return Path(self.filings_dir)
    
    def get_vector_db_path(self) -> Path:
        """Get Path object for vector database"""
        return Path(self.vector_db_path)
    
    def get_data_path(self) -> Path:
        """Get Path object for data directory"""
        return Path(self.data_dir)


# Create settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"Warning: Error loading settings: {e}")
    print("Creating settings with defaults. Please set OPENAI_API_KEY in .env file for LLM features.")
    # Create with minimal defaults
    import os
    os.environ.setdefault("OPENAI_API_KEY", "")
    settings = Settings()

