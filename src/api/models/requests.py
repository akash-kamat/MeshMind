from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum

class FileUploadRequest(BaseModel):
    index_name: Optional[str] = Field(default="default", description="Name of the index to store documents")
    
class URLScrapeRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL to scrape")
    index_name: Optional[str] = Field(default="default", description="Name of the index to store content")
    
class WebsiteCrawlRequest(BaseModel):
    url: HttpUrl = Field(..., description="Base URL to crawl")
    max_pages: int = Field(default=10, ge=1, le=100, description="Maximum number of pages to crawl")
    index_name: Optional[str] = Field(default="default", description="Name of the index to store content")

class BatchURLsRequest(BaseModel):
    urls: List[HttpUrl] = Field(..., description="List of URLs to scrape")
    index_name: Optional[str] = Field(default="default", description="Name of the index to store content")

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message/question")
    index_name: Optional[str] = Field(default="default", description="Name of the index to query")
    stream: Optional[bool] = Field(default=False, description="Whether to stream the response")
    system_prompt: Optional[str] = Field(default=None, description="Custom system prompt")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    index_name: Optional[str] = Field(default="default", description="Name of the index to search")
    top_k: Optional[int] = Field(default=5, ge=1, le=50, description="Number of results to return")
    search_type: Optional[str] = Field(default="semantic", description="Type of search: semantic or hybrid")

class IndexCreateRequest(BaseModel):
    name: str = Field(..., description="Name of the index to create")
    dimension: Optional[int] = Field(default=768, description="Dimension of the vectors")

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"