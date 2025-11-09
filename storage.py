"""Storage layer for queuectl using SQLite."""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from job import Job, JobState


class JobStorage:
    """SQLite-based job storage."""
    
    def __init__(self, db_file: str = "queuectl.db"):
        """Initialize storage with SQLite database."""
        self.db_file = Path(db_file)
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(str(self.db_file))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self) -> None:
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 3,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error_message TEXT
                )
            """)
            
            # Dead Letter Queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dlq (
                    id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    max_retries INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    moved_at TEXT NOT NULL,
                    error_message TEXT,
                    FOREIGN KEY (id) REFERENCES jobs(id)
                )
            """)
            
            # Index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_state 
                ON jobs(state)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_created_at 
                ON jobs(created_at)
            """)
    
    def add_job(self, job: Job) -> None:
        """Add a new job to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO jobs (id, command, state, attempts, max_retries, 
                                created_at, updated_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.id,
                job.command,
                job.state.value,
                job.attempts,
                job.max_retries,
                job.created_at,
                job.updated_at,
                job.error_message,
            ))
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_job(row)
            return None
    
    def get_next_pending_job(self) -> Optional[Job]:
        """Get the next pending job (FIFO) and atomically mark it as processing."""
        from utils import current_timestamp
        # Use a separate connection with immediate locking to prevent race conditions
        conn = sqlite3.connect(str(self.db_file), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.isolation_level = None  # Manual transaction control
        cursor = conn.cursor()
        try:
            # Begin immediate transaction (acquires write lock)
            cursor.execute("BEGIN IMMEDIATE")
            try:
                # Get the first pending job ID
                cursor.execute("""
                    SELECT id FROM jobs 
                    WHERE state = ? 
                    ORDER BY created_at ASC 
                    LIMIT 1
                """, (JobState.PENDING.value,))
                row = cursor.fetchone()
                if row:
                    job_id = row["id"]
                    # Atomically update to processing (only if still pending)
                    cursor.execute("""
                        UPDATE jobs 
                        SET state = ?, updated_at = ?
                        WHERE id = ? AND state = ?
                    """, (JobState.PROCESSING.value, current_timestamp(), 
                          job_id, JobState.PENDING.value))
                    # Check if update was successful (prevents race conditions)
                    if cursor.rowcount > 0:
                        cursor.execute("COMMIT")
                        # Fetch the full job record
                        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                        updated_row = cursor.fetchone()
                        if updated_row:
                            job = self._row_to_job(updated_row)
                            return job
                    else:
                        # Another worker got this job first
                        cursor.execute("ROLLBACK")
                        return None
                else:
                    cursor.execute("COMMIT")
                return None
            except Exception:
                cursor.execute("ROLLBACK")
                raise
        finally:
            conn.close()
    
    def update_job_state(self, job_id: str, new_state: JobState, 
                        error_message: Optional[str] = None) -> None:
        """Update job state."""
        from utils import current_timestamp
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs 
                SET state = ?, updated_at = ?, error_message = ?
                WHERE id = ?
            """, (new_state.value, current_timestamp(), error_message, job_id))
    
    def increment_attempts(self, job_id: str) -> None:
        """Increment job attempts counter."""
        from utils import current_timestamp
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs 
                SET attempts = attempts + 1, updated_at = ?
                WHERE id = ?
            """, (current_timestamp(), job_id))
            cursor.execute("SELECT attempts FROM jobs WHERE id = ?", (job_id,))
            result = cursor.fetchone()
            if result:
                return result["attempts"]
    
    def move_to_dlq(self, job: Job) -> None:
        """Move a job to the Dead Letter Queue."""
        from utils import current_timestamp
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Remove from jobs table
            cursor.execute("DELETE FROM jobs WHERE id = ?", (job.id,))
            
            # Add to DLQ
            cursor.execute("""
                INSERT INTO dlq (id, command, attempts, max_retries, 
                               created_at, moved_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                job.id,
                job.command,
                job.attempts,
                job.max_retries,
                job.created_at,
                current_timestamp(),
                job.error_message,
            ))
    
    def list_jobs(self, state: Optional[JobState] = None, 
                  limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List jobs, optionally filtered by state."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM jobs"
            params = []
            
            if state:
                query += " WHERE state = ?"
                params.append(state.value)
            
            query += " ORDER BY created_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def list_dlq(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List jobs in Dead Letter Queue."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM dlq ORDER BY moved_at DESC"
            if limit:
                query += " LIMIT ?"
                cursor.execute(query, (limit,))
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_dlq_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job from DLQ by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dlq WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def retry_dlq_job(self, job_id: str) -> bool:
        """Move a job from DLQ back to jobs table as pending."""
        dlq_job = self.get_dlq_job(job_id)
        if not dlq_job:
            return False
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Remove from DLQ
            cursor.execute("DELETE FROM dlq WHERE id = ?", (job_id,))
            
            # Add back to jobs as pending
            from utils import current_timestamp
            cursor.execute("""
                INSERT INTO jobs (id, command, state, attempts, max_retries, 
                                created_at, updated_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dlq_job["id"],
                dlq_job["command"],
                JobState.PENDING.value,
                0,  # Reset attempts
                dlq_job["max_retries"],
                dlq_job["created_at"],
                current_timestamp(),
                None,  # Clear error message
            ))
            return True
    
    def _row_to_job(self, row: sqlite3.Row) -> Job:
        """Convert database row to Job object."""
        return Job(
            id=row["id"],
            command=row["command"],
            state=JobState(row["state"]),
            attempts=row["attempts"],
            max_retries=row["max_retries"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"],
        )
    
    def get_stats(self) -> Dict[str, int]:
        """Get job statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            stats = {}
            
            for state in JobState:
                cursor.execute("SELECT COUNT(*) as count FROM jobs WHERE state = ?", 
                             (state.value,))
                result = cursor.fetchone()
                stats[state.value] = result["count"] if result else 0
            
            cursor.execute("SELECT COUNT(*) as count FROM dlq")
            result = cursor.fetchone()
            stats["dlq"] = result["count"] if result else 0
            
            return stats

