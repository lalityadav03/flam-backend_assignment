"""Worker management for queuectl."""

import subprocess
import threading
import time
from typing import Optional, List
from job import Job, JobState
from storage import JobStorage
from config import ConfigManager
from utils import current_timestamp


class WorkerManager:
    """Manage worker threads for processing jobs."""
    
    def __init__(self, storage: JobStorage, config: ConfigManager):
        """Initialize worker manager."""
        self.storage = storage
        self.config = config
        self.workers: List[Worker] = []
        self.running = False
        self.lock = threading.Lock()
    
    def start_workers(self, count: int = 1) -> None:
        """Start N worker threads."""
        with self.lock:
            if self.running:
                print(f"Workers are already running. Current count: {len(self.workers)}")
                return
            
            self.running = True
            self.workers = []
            
            for i in range(count):
                worker = Worker(i + 1, self.storage, self.config, self)
                worker.start()
                self.workers.append(worker)
                print(f"Started worker {i + 1}")
            
            print(f"Started {count} worker(s)")
    
    def stop_workers(self) -> None:
        """Stop all workers gracefully."""
        with self.lock:
            if not self.running:
                print("No workers are running.")
                return
            
            self.running = False
            
            # Wait for workers to finish
            for worker in self.workers:
                worker.stop()
            
            for worker in self.workers:
                worker.join(timeout=5.0)
            
            self.workers = []
            print("All workers stopped.")
    
    def is_running(self) -> bool:
        """Check if workers are running."""
        return self.running
    
    def get_worker_count(self) -> int:
        """Get current worker count."""
        return len(self.workers)


class Worker(threading.Thread):
    """Worker thread for processing jobs."""
    
    def __init__(self, worker_id: int, storage: JobStorage, 
                 config: ConfigManager, manager: WorkerManager):
        """Initialize worker."""
        super().__init__(daemon=True, name=f"Worker-{worker_id}")
        self.worker_id = worker_id
        self.storage = storage
        self.config = config
        self.manager = manager
        self.stop_event = threading.Event()
    
    def stop(self) -> None:
        """Signal worker to stop."""
        self.stop_event.set()
    
    def run(self) -> None:
        """Main worker loop."""
        while not self.stop_event.is_set() and self.manager.running:
            job = self.storage.get_next_pending_job()
            
            if job:
                self.process_job(job)
            else:
                # No jobs available, sleep briefly
                time.sleep(0.5)
    
    def process_job(self, job: Job) -> None:
        """Process a single job."""
        # Job is already marked as processing by get_next_pending_job
        try:
            # Execute command
            result = subprocess.run(
                job.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Success
                self.storage.update_job_state(job.id, JobState.COMPLETED)
                print(f"[Worker {self.worker_id}] Job {job.id} completed successfully")
            else:
                # Failure
                self.handle_job_failure(job, result.stderr or result.stdout or "Unknown error")
        
        except subprocess.TimeoutExpired:
            self.handle_job_failure(job, "Job execution timed out")
        
        except Exception as e:
            self.handle_job_failure(job, str(e))
    
    def handle_job_failure(self, job: Job, error_message: str) -> None:
        """Handle job failure with retry logic."""
        # Increment attempts
        self.storage.increment_attempts(job.id)
        
        # Get updated job
        updated_job = self.storage.get_job(job.id)
        if not updated_job:
            return
        
        if updated_job.attempts >= updated_job.max_retries:
            # Max retries reached, move to DLQ
            updated_job.update_state(JobState.DEAD, error_message)
            self.storage.move_to_dlq(updated_job)
            print(f"[Worker {self.worker_id}] Job {job.id} moved to DLQ after {updated_job.attempts} attempts")
        else:
            # Calculate exponential backoff delay
            backoff_base = self.config.get("backoff_base", 2)
            delay = backoff_base ** updated_job.attempts
            
            # Mark as failed and update error message
            self.storage.update_job_state(job.id, JobState.FAILED, error_message)
            
            print(f"[Worker {self.worker_id}] Job {job.id} failed (attempt {updated_job.attempts}/{updated_job.max_retries}). "
                  f"Retrying in {delay} seconds...")
            
            # Wait for backoff delay
            if self.stop_event.wait(timeout=delay):
                # Stop was requested during backoff
                return
            
            # Reset to pending for retry
            self.storage.update_job_state(job.id, JobState.PENDING)


# Global worker manager instance
_worker_manager: Optional[WorkerManager] = None


def get_worker_manager(storage: JobStorage, config: ConfigManager) -> WorkerManager:
    """Get or create global worker manager."""
    global _worker_manager
    if _worker_manager is None:
        _worker_manager = WorkerManager(storage, config)
    return _worker_manager

