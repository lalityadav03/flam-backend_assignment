"""Dead Letter Queue management for queuectl."""

from typing import List, Dict, Any, Optional
from storage import JobStorage
from utils import print_table


class DLQManager:
    """Manage Dead Letter Queue operations."""
    
    def __init__(self, storage: JobStorage):
        """Initialize DLQ manager."""
        self.storage = storage
    
    def list_jobs(self, limit: Optional[int] = None) -> None:
        """List all jobs in DLQ."""
        jobs = self.storage.list_dlq(limit)
        
        if not jobs:
            print("Dead Letter Queue is empty.")
            return
        
        # Format for display
        formatted_jobs = []
        for job in jobs:
            formatted_jobs.append({
                "ID": job["id"],
                "Command": job["command"][:50] + "..." if len(job["command"]) > 50 else job["command"],
                "Attempts": job["attempts"],
                "Max Retries": job["max_retries"],
                "Moved At": job["moved_at"],
                "Error": job["error_message"][:50] + "..." if job["error_message"] and len(job["error_message"]) > 50 else (job["error_message"] or "N/A"),
            })
        
        print_table(formatted_jobs, headers=["ID", "Command", "Attempts", "Max Retries", "Moved At", "Error"])
        print(f"\nTotal: {len(jobs)} job(s) in DLQ")
    
    def retry_job(self, job_id: str) -> bool:
        """Retry a job from DLQ."""
        success = self.storage.retry_dlq_job(job_id)
        if success:
            print(f"Job {job_id} moved back to pending queue.")
            return True
        else:
            print(f"Job {job_id} not found in DLQ.")
            return False

