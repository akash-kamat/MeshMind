from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional
import tempfile
import os
import asyncio
import logging

from ..models.requests import URLScrapeRequest, WebsiteCrawlRequest, BatchURLsRequest
from ..models.responses import JobResponse, JobStatusResponse, FileUploadResponse, IngestionResult
from ...core.ingestion import get_ingestion_pipeline
from ...utils.scraper import get_scraper
from ...utils.jobs import get_job_manager, run_job_with_progress
from ...utils.parser import get_parser

router = APIRouter(prefix="/ingest", tags=["ingestion"])
logger = logging.getLogger(__name__)

@router.post("/files", response_model=JobResponse)
async def ingest_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    index_name: Optional[str] = Form("default")
):
    try:
        job_manager = get_job_manager()
        job_id = job_manager.create_job("file_ingestion")
        
        file_paths = []
        parser = get_parser()
        
        for file in files:
            if not parser.is_supported(file.filename):
                job_manager.fail_job(job_id, f"Unsupported file type: {file.filename}")
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                file_paths.append(tmp_file.name)
        
        pipeline = get_ingestion_pipeline()
        background_tasks.add_task(
            run_job_with_progress,
            job_id,
            pipeline.ingest_files,
            file_paths,
            index_name
        )
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message=f"Started processing {len(files)} files"
        )
        
    except Exception as e:
        logger.error(f"File ingestion failed: {e}")
        if 'job_id' in locals():
            job_manager.fail_job(job_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/url", response_model=JobResponse)
async def ingest_url(
    request: URLScrapeRequest,
    background_tasks: BackgroundTasks
):
    try:
        job_manager = get_job_manager()
        job_id = job_manager.create_job("url_scraping")
        
        async def scrape_and_ingest(progress_callback=None):
            try:
                scraper = get_scraper()
                
                # Use the progress_callback if provided
                if progress_callback:
                    progress_callback("Starting URL scraping...", 0.1)
                
                scraped_data = scraper.scrape_single_url(str(request.url))
                if not scraped_data:
                    return {"success": False, "error": "Failed to scrape URL"}
                
                if progress_callback:
                    progress_callback("URL scraped, processing content...", 0.7)
                
                pipeline = get_ingestion_pipeline()
                result = await pipeline.ingest_content(
                    [scraped_data], 
                    request.index_name,
                    lambda msg, prog: progress_callback(msg, 0.7 + prog * 0.3) if progress_callback else None
                )
                
                return result
                
            except Exception as e:
                logger.error(f"URL scraping job {job_id} failed: {e}")
                return {"success": False, "error": str(e)}
        
        background_tasks.add_task(
            run_job_with_progress,
            job_id,
            scrape_and_ingest
        )
        
        return JobResponse(
            job_id=job_id,
            status="pending", 
            message=f"Started scraping URL: {request.url}"
        )
        
    except Exception as e:
        logger.error(f"URL ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/website", response_model=JobResponse)
async def ingest_website(
    request: WebsiteCrawlRequest,
    background_tasks: BackgroundTasks
):
    try:
        job_manager = get_job_manager()
        job_id = job_manager.create_job("website_crawling")
        
        async def crawl_and_ingest(progress_callback=None):
            try:
                scraper = get_scraper()
                
                # Create a website-specific progress callback that uses the job's callback
                website_progress = None
                if progress_callback:
                    progress_callback("Starting website crawl...", 0.1)
                    website_progress = lambda msg, prog: progress_callback(msg, prog * 0.8)
                
                scraped_data = await scraper.crawl_website(
                    str(request.url), 
                    request.max_pages,
                    website_progress
                )
                
                if not scraped_data:
                    return {"success": False, "error": "Failed to crawl website"}
                
                if progress_callback:
                    progress_callback("Website crawled, processing content...", 0.8)
                
                pipeline = get_ingestion_pipeline()
                result = await pipeline.ingest_content(
                    scraped_data,
                    request.index_name,
                    lambda msg, prog: progress_callback(msg, 0.8 + prog * 0.2) if progress_callback else None
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Website crawling job {job_id} failed: {e}")
                return {"success": False, "error": str(e)}
        
        background_tasks.add_task(
            run_job_with_progress,
            job_id,
            crawl_and_ingest
        )
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message=f"Started crawling website: {request.url} (max {request.max_pages} pages)"
        )
        
    except Exception as e:
        logger.error(f"Website ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_ingestion_status(job_id: str):
    try:
        job_manager = get_job_manager()
        job_status = job_manager.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(**job_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))