"""Job class for queuectl."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from utils import generate_id, current_timestamp


class JobState(Enum):
    """Job state enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"


@dataclass
class Job:
    """Job data class."""
    id: str = field(default_factory=generate_id)
    command: str = ""
    state: JobState = JobState.PENDING
    attempts: int = 0
    max_retries: int = 3
    created_at: str = field(default_factory=current_timestamp)
    updated_at: str = field(default_factory=current_timestamp)
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert job to dictionary."""
        return {
            "id": self.id,
            "command": self.command,
            "state": self.state.value,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        """Create job from dictionary."""
        job = cls(
            id=data["id"],
            command=data["command"],
            state=JobState(data["state"]),
            attempts=data["attempts"],
            max_retries=data["max_retries"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            error_message=data.get("error_message"),
        )
        return job
    
    def update_state(self, new_state: JobState, error_message: Optional[str] = None) -> None:
        """Update job state and timestamp."""
        self.state = new_state
        self.updated_at = current_timestamp()
        if error_message:
            self.error_message = error_message
    
    def increment_attempts(self) -> None:
        """Increment attempt counter."""
        self.attempts += 1
        self.updated_at = current_timestamp()
    
    def should_retry(self) -> bool:
        """Check if job should be retried."""
        return self.attempts < self.max_retries and self.state != JobState.DEAD
    
    def can_retry(self) -> bool:
        """Check if job can be retried (is in failed state and has retries left)."""
        return (
            self.state == JobState.FAILED and 
            self.attempts < self.max_retries
        )

