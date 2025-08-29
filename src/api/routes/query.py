from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import logging

from ..models.requests import ChatRequest, SearchRequest
from ..models.responses import ChatResponse, SearchResponse, SearchResult
from ...core.retrieval import get_query_engine

router = APIRouter(prefix="/query", tags=["querying"])
logger = logging.getLogger(__name__)

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        query_engine = get_query_engine()
        
        if request.stream:
            async def generate_stream() -> AsyncGenerator[str, None]:
                try:
                    async for chunk in query_engine.streaming_chat(
                        request.message, 
                        request.index_name or "default",
                        request.system_prompt
                    ):
                        yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                    
                    yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                    
                except Exception as e:
                    logger.error(f"Streaming chat error: {e}")
                    yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        else:
            result = query_engine.chat(
                request.message,
                request.index_name or "default", 
                request.system_prompt
            )
            
            return ChatResponse(**result)
            
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    try:
        query_engine = get_query_engine()
        
        if request.search_type == "hybrid":
            results = query_engine.hybrid_search(
                request.query,
                request.index_name or "default",
                request.top_k
            )
        else:
            results = query_engine.semantic_search(
                request.query,
                request.index_name or "default", 
                request.top_k
            )
        
        search_results = [SearchResult(**result) for result in results]
        
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=request.query,
            index_name=request.index_name or "default",
            search_type=request.search_type or "semantic"
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))