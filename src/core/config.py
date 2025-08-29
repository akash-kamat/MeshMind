from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    pinecone_api_key: str
    google_api_key: str 
    firecrawl_api_key: str
    
    pinecone_index_name: str = "rag-system"
    pinecone_environment: str = "us-east1-gcp"
    
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_results: int = 5
    
    api_host: str = "localhost"
    api_port: int = 8000
    streamlit_port: int = 8501
    
    python_version: str = "3.11"

def get_settings() -> Settings:
    return Settings()

settings = get_settings()