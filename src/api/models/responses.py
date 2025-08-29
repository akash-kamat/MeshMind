from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from .requests import JobStatus

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str = "Job created successfully"

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress as a percentage (0.0 to 1.0)")
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class IngestionResult(BaseModel):
    success: bool
    documents_processed: int
    chunks_created: int
    index_name: str
    processing_time: Optional[float] = None

class SearchResult(BaseModel):
    content: str
    score: float
    metadata: Dict[str, Any]
    node_id: str
    source: str

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str
    index_name: str
    search_type: str

class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class IndexInfo(BaseModel):
    name: str
    doc_count: int
    total_vector_count: int
    dimension: int
    created_at: datetime
    index_fullness: float

class IndexListResponse(BaseModel):
    indexes: List[IndexInfo]

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, str]
    timestamp: datetime
    version: str = "0.1.0"

class FileUploadResponse(BaseModel):
    files_processed: List[str]
    job_id: str
    message: str