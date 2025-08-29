from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
import asyncio
import google.generativeai as genai

from .vectorstore import get_pinecone_manager
from .embeddings import get_embeddings
from .config import settings

logger = logging.getLogger(__name__)

class QueryEngine:
    def __init__(self):
        self.vectorstore = get_pinecone_manager()
        self.embeddings = get_embeddings()
        # Configure Gemini directly
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel("models/gemini-1.5-flash")
        
    def get_retriever(self, index_name: str, similarity_top_k: int = None) -> Optional[VectorIndexRetriever]:
        try:
            if not similarity_top_k:
                similarity_top_k = settings.top_k_results
                
            index = self.vectorstore.load_vector_index(index_name)
            if not index:
                logger.error(f"Could not load index: {index_name}")
                return None
                
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=similarity_top_k
            )
            
            return retriever
            
        except Exception as e:
            logger.error(f"Failed to create retriever for {index_name}: {e}")
            return None
    
    def semantic_search(
        self, 
        query: str, 
        index_name: str, 
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        try:
            if not top_k:
                top_k = settings.top_k_results
                
            retriever = self.get_retriever(index_name, top_k)
            if not retriever:
                return []
            
            nodes = retriever.retrieve(query)
            
            results = []
            for node in nodes:
                result = {
                    'content': node.text,
                    'score': node.score if hasattr(node, 'score') else 0.0,
                    'metadata': node.metadata,
                    'node_id': node.node_id,
                    'source': node.metadata.get('file_name', 'Unknown')
                }
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def hybrid_search(
        self, 
        query: str, 
        index_name: str, 
        top_k: int = None,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        try:
            semantic_results = self.semantic_search(query, index_name, top_k)
            
            return semantic_results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
    
    def create_query_engine(self, index_name: str) -> Optional[RetrieverQueryEngine]:
        try:
            retriever = self.get_retriever(index_name)
            if not retriever:
                return None
            
            # For now, return the retriever - we'll handle LLM separately
            return retriever
            
        except Exception as e:
            logger.error(f"Failed to create query engine: {e}")
            return None
    
    async def streaming_chat(
        self, 
        message: str, 
        index_name: str,
        system_prompt: str = None
    ) -> AsyncGenerator[str, None]:
        try:
            if not system_prompt:
                system_prompt = """You are a helpful AI assistant that answers questions based on the provided context. 
                Use only the information from the context to answer questions. If you cannot find the answer in the context, 
                say so clearly. Provide detailed and accurate answers when possible."""
            
            # Get relevant context
            search_results = self.semantic_search(message, index_name, 5)
            if not search_results:
                yield "No relevant information found in the knowledge base."
                return
            
            # Build context from search results
            context = "\n\n".join([f"Source: {result['source']}\nContent: {result['content']}" for result in search_results])
            
            # Create prompt with context
            full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nQuestion: {message}\n\nAnswer:"
            
            # Generate streaming response
            response = self.model.generate_content(full_prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Streaming chat failed: {e}")
            yield f"Error: {str(e)}"
    
    def chat(
        self, 
        message: str, 
        index_name: str,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        try:
            if not system_prompt:
                system_prompt = """You are a helpful AI assistant that answers questions based on the provided context. 
                Use only the information from the context to answer questions. If you cannot find the answer in the context, 
                say so clearly. Provide detailed and accurate answers when possible."""
            
            # Get relevant context
            search_results = self.semantic_search(message, index_name, 5)
            if not search_results:
                return {
                    "response": "No relevant information found in the knowledge base.",
                    "sources": []
                }
            
            # Build context from search results
            context = "\n\n".join([f"Source: {result['source']}\nContent: {result['content']}" for result in search_results])
            
            # Create prompt with context
            full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nQuestion: {message}\n\nAnswer:"
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            # Format sources
            sources = []
            for result in search_results:
                source = {
                    'content': result['content'][:500] + "..." if len(result['content']) > 500 else result['content'],
                    'metadata': result['metadata'],
                    'score': result.get('score', 0.0)
                }
                sources.append(source)
            
            return {
                "response": response.text if response else "No response generated",
                "sources": sources,
                "metadata": {
                    "query": message,
                    "index_name": index_name
                }
            }
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {
                "response": f"Error: {str(e)}",
                "sources": []
            }
    
    def contextual_retrieval(
        self, 
        query: str, 
        index_name: str, 
        context_window: int = 3
    ) -> List[Dict[str, Any]]:
        try:
            results = self.semantic_search(query, index_name)
            
            enhanced_results = []
            for result in results:
                enhanced_result = result.copy()
                enhanced_result['context_enhanced'] = True
                enhanced_results.append(enhanced_result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Contextual retrieval failed: {e}")
            return []

def get_query_engine() -> QueryEngine:
    return QueryEngine()