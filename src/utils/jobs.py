import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Job:
    def __init__(self, job_id: str, job_type: str):
        self.job_id = job_id
        self.job_type = job_type
        self.status = JobStatus.PENDING
        self.progress = 0.0
        self.message = "Job created"
        self.created_at = datetime.utcnow()
        self.completed_at = None
        self.result = None
        self.error = None

    def update_progress(self, progress: float, message: str = None):
        self.progress = max(0.0, min(1.0, progress))
        if message:
            self.message = message
        logger.info(f"Job {self.job_id}: {self.progress:.1%} - {self.message}")

    def complete(self, result: Any = None):
        self.status = JobStatus.COMPLETED
        self.progress = 1.0
        self.completed_at = datetime.utcnow()
        self.result = result
        self.message = "Job completed successfully"
        logger.info(f"Job {self.job_id} completed")

    def fail(self, error: str):
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error
        self.message = f"Job failed: {error}"
        logger.error(f"Job {self.job_id} failed: {error}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error
        }

class JobManager:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        
    def create_job(self, job_type: str) -> str:
        job_id = str(uuid.uuid4())
        job = Job(job_id, job_type)
        self._jobs[job_id] = job
        logger.info(f"Created job {job_id} of type {job_type}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)
    
    def update_job_progress(self, job_id: str, progress: float, message: str = None):
        job = self.get_job(job_id)
        if job and job.status == JobStatus.PROCESSING:
            job.update_progress(progress, message)
    
    def start_job(self, job_id: str):
        job = self.get_job(job_id)
        if job:
            job.status = JobStatus.PROCESSING
            job.message = "Job started"
            logger.info(f"Started job {job_id}")
    
    def complete_job(self, job_id: str, result: Any = None):
        job = self.get_job(job_id)
        if job:
            job.complete(result)
    
    def fail_job(self, job_id: str, error: str):
        job = self.get_job(job_id)
        if job:
            job.fail(error)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self.get_job(job_id)
        return job.to_dict() if job else None
    
    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        jobs = sorted(self._jobs.values(), key=lambda x: x.created_at, reverse=True)
        return [job.to_dict() for job in jobs[:limit]]
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        now = datetime.utcnow()
        to_remove = []
        
        for job_id, job in self._jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                if job.completed_at:
                    age = (now - job.completed_at).total_seconds() / 3600
                    if age > max_age_hours:
                        to_remove.append(job_id)
        
        for job_id in to_remove:
            del self._jobs[job_id]
            logger.info(f"Cleaned up old job {job_id}")
        
        return len(to_remove)

job_manager = JobManager()

async def run_job_with_progress(
    job_id: str,
    job_func: Callable,
    *args, 
    **kwargs
):
    job_manager.start_job(job_id)
    
    def progress_callback(message: str, progress: float):
        job_manager.update_job_progress(job_id, progress, message)
    
    try:
        kwargs['progress_callback'] = progress_callback
        result = await job_func(*args, **kwargs)
        
        if isinstance(result, dict) and result.get('success', False):
            job_manager.complete_job(job_id, result)
        else:
            error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
            job_manager.fail_job(job_id, error_msg)
            
    except Exception as e:
        logger.error(f"Job {job_id} failed with exception: {e}")
        job_manager.fail_job(job_id, str(e))

def get_job_manager() -> JobManager:
    return job_manager