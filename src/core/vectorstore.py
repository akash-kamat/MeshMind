from pinecone import Pinecone, ServerlessSpec
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.schema import BaseNode
from typing import List, Optional, Dict, Any
import logging
from .config import settings
from .embeddings import get_embeddings

logger = logging.getLogger(__name__)

class PineconeManager:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.embeddings = get_embeddings()
        
    def create_index(self, index_name: str, dimension: int = 768) -> bool:
        try:
            if index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=index_name,
                    dimension=dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws", 
                        region="us-east-1"
                    )
                )
                logger.info(f"Created index: {index_name}")
                return True
            logger.info(f"Index {index_name} already exists")
            return True
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False
    
    def delete_index(self, index_name: str) -> bool:
        try:
            if index_name in self.pc.list_indexes().names():
                self.pc.delete_index(index_name)
                logger.info(f"Deleted index: {index_name}")
                return True
            logger.warning(f"Index {index_name} does not exist")
            return False
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            return False
    
    def list_indexes(self) -> List[str]:
        try:
            return self.pc.list_indexes().names()
        except Exception as e:
            logger.error(f"Failed to list indexes: {e}")
            return []
    
    def get_vector_store(self, index_name: str) -> Optional[PineconeVectorStore]:
        try:
            if index_name not in self.pc.list_indexes().names():
                if not self.create_index(index_name):
                    return None
            
            pinecone_index = self.pc.Index(index_name)
            vector_store = PineconeVectorStore(
                pinecone_index=pinecone_index,
                text_key="content"
            )
            return vector_store
        except Exception as e:
            logger.error(f"Failed to get vector store for {index_name}: {e}")
            return None
    
    def create_vector_index(self, index_name: str, nodes: List[BaseNode]) -> Optional[VectorStoreIndex]:
        try:
            vector_store = self.get_vector_store(index_name)
            if not vector_store:
                return None
                
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            index = VectorStoreIndex(
                nodes=nodes,
                storage_context=storage_context,
                embed_model=self.embeddings.embed_model
            )
            
            logger.info(f"Created vector index with {len(nodes)} nodes")
            return index
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            return None
    
    def load_vector_index(self, index_name: str) -> Optional[VectorStoreIndex]:
        try:
            vector_store = self.get_vector_store(index_name)
            if not vector_store:
                return None
                
            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=self.embeddings.embed_model
            )
            return index
        except Exception as e:
            logger.error(f"Failed to load vector index {index_name}: {e}")
            return None
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        try:
            if index_name not in self.pc.list_indexes().names():
                return {"error": "Index does not exist"}
                
            pinecone_index = self.pc.Index(index_name)
            stats = pinecone_index.describe_index_stats()
            
            # Create a clean dictionary with just the data we need
            # This avoids serialization issues with internal Pinecone SDK objects
            result = {}
            
            # Extract values safely, converting any objects to their string representation if needed
            if hasattr(stats, 'total_vector_count'):
                # Object-style access (newer Pinecone SDK)
                result["total_vector_count"] = int(stats.total_vector_count)
                
                if hasattr(stats, 'dimension'):
                    result["dimension"] = int(stats.dimension)
                else:
                    result["dimension"] = 768  # Default dimension
                    
                if hasattr(stats, 'namespaces'):
                    # Convert namespaces to a simple dictionary structure
                    namespaces_dict = {}
                    for ns_name, ns_data in stats.namespaces.items():
                        if hasattr(ns_data, 'vector_count'):
                            namespaces_dict[ns_name] = {'vector_count': int(ns_data.vector_count)}
                        else:
                            namespaces_dict[ns_name] = {'vector_count': 0}
                    result["namespaces"] = namespaces_dict
                else:
                    result["namespaces"] = {}
                
                # Add other fields that might be in the response
                if hasattr(stats, 'index_fullness'):
                    result["index_fullness"] = float(stats.index_fullness)
                else:
                    result["index_fullness"] = 0.0
                    
                if hasattr(stats, 'metric'):
                    result["metric"] = str(stats.metric)
                if hasattr(stats, 'vector_type'):
                    result["vector_type"] = str(stats.vector_type)
                    
            else:
                # Dictionary-style access (older Pinecone SDK or dict response)
                result = {
                    "total_vector_count": int(stats.get("total_vector_count", 0)),
                    "dimension": int(stats.get("dimension", 768)),
                    "namespaces": stats.get("namespaces", {}),
                    "index_fullness": float(stats.get("index_fullness", 0.0))
                }
                
                if "metric" in stats:
                    result["metric"] = str(stats["metric"])
                if "vector_type" in stats:
                    result["vector_type"] = str(stats["vector_type"])
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get stats for {index_name}: {e}")
            return {"error": str(e)}

def get_pinecone_manager() -> PineconeManager:
    return PineconeManager()