from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from ..models.responses import HealthResponse
from ...core.config import settings
from ...core.vectorstore import get_pinecone_manager
from ...core.embeddings import get_embeddings

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=HealthResponse)
async def health_check():
    try:
        services = {}
        
        try:
            pinecone_manager = get_pinecone_manager()
            indexes = pinecone_manager.list_indexes()
            services["pinecone"] = "healthy"
        except Exception as e:
            services["pinecone"] = f"unhealthy: {str(e)}"
            logger.error(f"Pinecone health check failed: {e}")
        
        try:
            embeddings = get_embeddings()
            test_embedding = embeddings.get_text_embedding("test")
            services["embeddings"] = "healthy" if len(test_embedding) > 0 else "unhealthy"
        except Exception as e:
            services["embeddings"] = f"unhealthy: {str(e)}"
            logger.error(f"Embeddings health check failed: {e}")
        
        overall_status = "healthy" if all("healthy" in status for status in services.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            services=services,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/ping")
async def ping():
    return {"status": "ok", "timestamp": datetime.utcnow()}