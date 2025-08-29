from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List
import logging

from ..models.requests import IndexCreateRequest
from ..models.responses import IndexListResponse, IndexInfo, SuccessResponse
from ...core.vectorstore import get_pinecone_manager

router = APIRouter(prefix="/indexes", tags=["index management"])
logger = logging.getLogger(__name__)

@router.get("/list", response_model=IndexListResponse)
async def list_indexes():
    try:
        pinecone_manager = get_pinecone_manager()
        index_names = pinecone_manager.list_indexes()
        
        indexes = []
        for name in index_names:
            try:
                stats = pinecone_manager.get_index_stats(name)
                
                if "error" not in stats:
                    index_info = IndexInfo(
                        name=name,
                        doc_count=stats.get("total_vector_count", 0),
                        total_vector_count=stats.get("total_vector_count", 0),
                        dimension=stats.get("dimension", 768),
                        created_at=datetime.utcnow(),  # Pinecone doesn't provide creation time
                        index_fullness=stats.get("index_fullness", 0.0)
                    )
                    indexes.append(index_info)
                else:
                    logger.warning(f"Could not get stats for index {name}: {stats['error']}")
                    
            except Exception as e:
                logger.error(f"Error getting stats for index {name}: {e}")
                continue
        
        return IndexListResponse(indexes=indexes)
        
    except Exception as e:
        logger.error(f"Failed to list indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create", response_model=SuccessResponse)
async def create_index(request: IndexCreateRequest):
    try:
        pinecone_manager = get_pinecone_manager()
        
        success = pinecone_manager.create_index(request.name, request.dimension)
        
        if success:
            return SuccessResponse(
                message=f"Index '{request.name}' created successfully",
                data={"name": request.name, "dimension": request.dimension}
            )
        else:
            raise HTTPException(status_code=400, detail=f"Failed to create index '{request.name}'")
            
    except Exception as e:
        logger.error(f"Failed to create index: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{index_name}", response_model=SuccessResponse)
async def delete_index(index_name: str):
    try:
        pinecone_manager = get_pinecone_manager()
        
        success = pinecone_manager.delete_index(index_name)
        
        if success:
            return SuccessResponse(
                message=f"Index '{index_name}' deleted successfully"
            )
        else:
            raise HTTPException(status_code=404, detail=f"Index '{index_name}' not found")
            
    except Exception as e:
        logger.error(f"Failed to delete index: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{index_name}/stats")
async def get_index_stats(index_name: str):
    try:
        pinecone_manager = get_pinecone_manager()
        stats = pinecone_manager.get_index_stats(index_name)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail=stats["error"])
        
        # Return a clean dictionary that's guaranteed to be JSON-serializable
        return {
            "total_vector_count": stats.get("total_vector_count", 0),
            "dimension": stats.get("dimension", 768),
            "namespaces": stats.get("namespaces", {}),
            "index_fullness": stats.get("index_fullness", 0.0),
            "metric": stats.get("metric", "cosine"),
            "vector_type": stats.get("vector_type", "dense")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))