from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core.base.embeddings.base import BaseEmbedding
from .config import settings
import google.generativeai as genai

class GeminiEmbeddings:
    def __init__(self):
        genai.configure(api_key=settings.google_api_key)
        self._embed_model = GeminiEmbedding(
            model_name="models/text-embedding-004",
            api_key=settings.google_api_key
        )
    
    @property
    def embed_model(self) -> BaseEmbedding:
        return self._embed_model
    
    def get_text_embedding(self, text: str) -> list[float]:
        return self._embed_model.get_text_embedding(text)
    
    async def aget_text_embedding(self, text: str) -> list[float]:
        return await self._embed_model.aget_text_embedding(text)
    
    def get_query_embedding(self, query: str) -> list[float]:
        return self._embed_model.get_query_embedding(query)
    
    async def aget_query_embedding(self, query: str) -> list[float]:
        return await self._embed_model.aget_query_embedding(query)

def get_embeddings() -> GeminiEmbeddings:
    return GeminiEmbeddings()