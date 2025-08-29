from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document, BaseNode
from typing import List, Dict, Any, Optional, Callable
import logging
import uuid
import asyncio
from datetime import datetime

from .embeddings import get_embeddings
from .vectorstore import get_pinecone_manager
from .config import settings
from ..utils.parser import get_parser

logger = logging.getLogger(__name__)

class IngestionPipeline:
    def __init__(self):
        self.embeddings = get_embeddings()
        self.vectorstore = get_pinecone_manager()
        self.parser = get_parser()
        
        # Use simple sentence-based splitter instead of semantic splitter for faster processing
        # This splitter divides text based on sentences and paragraphs without semantic analysis
        self.splitter = SentenceSplitter(
            chunk_size=1024,      # Target chunk size in characters (adjust based on your needs)
            chunk_overlap=100,    # Overlap between chunks to maintain context across chunks
            paragraph_separator="\n\n",  # Identify paragraphs by double newlines
            secondary_chunking_regex="[^,.;。？！]+[,.;。？！]?"  # Regex for splitting by sentences
        )
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize metadata to ensure all values are compatible with Pinecone.
        Pinecone accepts: string, number, boolean, or list of strings.
        """
        sanitized = {}
        for key, value in metadata.items():
            if value is None:
                # Replace None values with empty string
                sanitized[key] = ""
            elif isinstance(value, (str, int, float, bool)):
                # These types are fine as is
                sanitized[key] = value
            elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                # List of strings is fine
                sanitized[key] = value
            elif isinstance(value, list):
                # Convert list of non-strings to list of strings
                sanitized[key] = [str(item) for item in value]
            else:
                # Convert any other type to string
                sanitized[key] = str(value)
        return sanitized
        
    def create_documents(self, parsed_data: List[Dict[str, Any]]) -> List[Document]:
        documents = []
        
        for data in parsed_data:
            # Create metadata dictionary and sanitize it
            metadata = {
                'title': data['title'],
                'file_path': data['file_path'],
                'file_name': data['file_name'],
                'file_size': data['file_size'],
                'file_type': data['file_type'],
                'mime_type': data['mime_type'],
                'ingestion_timestamp': datetime.utcnow().isoformat(),
                'document_id': str(uuid.uuid4()),
            }
            
            # Add additional metadata if available
            if 'metadata' in data and data['metadata']:
                metadata.update(data['metadata'])
                
            # Sanitize all metadata to ensure it's compatible with Pinecone
            sanitized_metadata = self._sanitize_metadata(metadata)
            
            doc = Document(
                text=data['content'],
                metadata=sanitized_metadata
            )
            documents.append(doc)
            
        return documents
    
    def create_text_chunks(self, documents: List[Document]) -> List[BaseNode]:
        try:
            all_nodes = []
            for doc in documents:
                nodes = self.splitter.get_nodes_from_documents([doc])
                
                for i, node in enumerate(nodes):
                    # Add additional metadata to each chunk
                    additional_metadata = {
                        'chunk_id': str(uuid.uuid4()),
                        'chunk_index': i,
                        'total_chunks': len(nodes),
                        'parent_doc_id': doc.metadata.get('document_id'),
                    }
                    
                    # Update the node metadata and sanitize it
                    updated_metadata = {**node.metadata, **additional_metadata}
                    node.metadata = self._sanitize_metadata(updated_metadata)
                
                all_nodes.extend(nodes)
                
            logger.info(f"Created {len(all_nodes)} text chunks from {len(documents)} documents")
            return all_nodes
            
        except Exception as e:
            logger.error(f"Failed to create text chunks: {e}")
            return []
    
    async def ingest_files(
        self, 
        file_paths: List[str], 
        index_name: str = None,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        try:
            if not index_name:
                index_name = settings.pinecone_index_name
                
            if progress_callback:
                progress_callback("Parsing files...", 0.1)
            
            parsed_data = self.parser.parse_files(file_paths)
            if not parsed_data:
                return {"success": False, "error": "No valid files to process"}
            
            if progress_callback:
                progress_callback("Creating documents...", 0.3)
                
            documents = self.create_documents(parsed_data)
            
            if progress_callback:
                progress_callback("Creating text chunks...", 0.5)
                
            nodes = self.create_text_chunks(documents)
            if not nodes:
                return {"success": False, "error": "Failed to create chunks"}
            
            if progress_callback:
                progress_callback("Storing in vector database...", 0.8)
                
            index = self.vectorstore.create_vector_index(index_name, nodes)
            if not index:
                return {"success": False, "error": "Failed to create vector index"}
            
            if progress_callback:
                progress_callback("Ingestion completed", 1.0)
            
            return {
                "success": True,
                "documents_processed": len(documents),
                "chunks_created": len(nodes),
                "index_name": index_name
            }
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def ingest_content(
        self,
        content_data: List[Dict[str, Any]],
        index_name: str = None,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        try:
            if not index_name:
                index_name = settings.pinecone_index_name
                
            if progress_callback:
                progress_callback("Processing content...", 0.2)
            
            documents = self.create_documents(content_data)
            
            if progress_callback:
                progress_callback("Creating text chunks...", 0.5)
                
            nodes = self.create_text_chunks(documents)
            if not nodes:
                return {"success": False, "error": "Failed to create chunks"}
            
            if progress_callback:
                progress_callback("Storing in vector database...", 0.8)
                
            index = self.vectorstore.create_vector_index(index_name, nodes)
            if not index:
                return {"success": False, "error": "Failed to create vector index"}
            
            if progress_callback:
                progress_callback("Ingestion completed", 1.0)
            
            return {
                "success": True,
                "documents_processed": len(documents),
                "chunks_created": len(nodes),
                "index_name": index_name
            }
            
        except Exception as e:
            logger.error(f"Content ingestion failed: {e}")
            return {"success": False, "error": str(e)}

def get_ingestion_pipeline() -> IngestionPipeline:
    return IngestionPipeline()