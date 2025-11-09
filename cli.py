"""CLI interface for queuectl using Click."""

import click
import json
from typing import Optional
from job import Job, JobState
from storage import JobStorage
from config import ConfigManager
from worker import WorkerManager, get_worker_manager
from dlq import DLQManager
from utils import print_table, current_timestamp


# Global instances
_storage: Optional[JobStorage] = None
_config: Optional[ConfigManager] = None


def get_storage() -> JobStorage:
    """Get or create storage instance."""
    global _storage
    if _storage is None:
        _storage = JobStorage()
    return _storage


def get_config() -> ConfigManager:
    """Get or create config instance."""
    global _config
    if _config is None:
        _config = ConfigManager()
    return _config


@click.group()
def cli():
    """queuectl - A CLI-based background job queue system."""
    pass


@cli.command()
@click.argument("job_data", type=str)
@click.option("--max-retries", type=int, help="Maximum number of retries")
def enqueue(job_data: str, max_retries: Optional[int] = None):
    """Enqueue a new job. JOB_DATA should be a JSON string with 'command' field."""
    try:
        data = json.loads(job_data)
        command = data.get("command")
        
        if not command:
            click.echo("Error: 'command' field is required in job data", err=True)
            return
        
        storage = get_storage()
        config = get_config()
        
        job = Job(
            command=command,
            max_retries=max_retries or config.get("max_retries", 3),
        )
        
        storage.add_job(job)
        click.echo(f"Job enqueued: {job.id}")
        click.echo(f"Command: {command}")
        
    except json.JSONDecodeError:
        click.echo("Error: Invalid JSON in job data", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.group()
def worker():
    """Manage workers."""
    pass


@worker.command()
@click.option("--count", default=1, type=int, help="Number of workers to start")
def start(count: int):
    """Start worker threads."""
    if count < 1:
        click.echo("Error: Worker count must be at least 1", err=True)
        return
    
    storage = get_storage()
    config = get_config()
    manager = get_worker_manager(storage, config)
    manager.start_workers(count)
    
    try:
        # Keep the main thread alive
        import time
        while manager.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\nStopping workers...")
        manager.stop_workers()


@worker.command()
def stop():
    """Stop all workers."""
    storage = get_storage()
    config = get_config()
    manager = get_worker_manager(storage, config)
    manager.stop_workers()


@cli.command()
@click.option("--state", type=click.Choice(["pending", "processing", "completed", "failed", "dead"]), 
              help="Filter jobs by state")
@click.option("--limit", type=int, help="Limit number of results")
def list(state: Optional[str], limit: Optional[int]):
    """List jobs."""
    storage = get_storage()
    
    job_state = None
    if state:
        job_state = JobState(state)
    
    jobs = storage.list_jobs(job_state, limit)
    
    if not jobs:
        click.echo("No jobs found.")
        return
    
    # Format for display
    formatted_jobs = []
    for job in jobs:
        formatted_jobs.append({
            "ID": job["id"],
            "Command": job["command"][:50] + "..." if len(job["command"]) > 50 else job["command"],
            "State": job["state"],
            "Attempts": job["attempts"],
            "Max Retries": job["max_retries"],
            "Created At": job["created_at"],
            "Updated At": job["updated_at"],
        })
    
    print_table(formatted_jobs, headers=["ID", "Command", "State", "Attempts", "Max Retries", "Created At", "Updated At"])


@cli.command()
def status():
    """Show queue status and statistics."""
    storage = get_storage()
    stats = storage.get_stats()
    
    click.echo("Queue Status:")
    click.echo("=" * 50)
    for state, count in stats.items():
        click.echo(f"{state.capitalize()}: {count}")
    click.echo("=" * 50)
    total = sum(count for state, count in stats.items() if state != "dlq")
    click.echo(f"Total Jobs: {total}")
    click.echo(f"DLQ Jobs: {stats.get('dlq', 0)}")


@cli.group()
def dlq():
    """Manage Dead Letter Queue."""
    pass


@dlq.command("list")
@click.option("--limit", type=int, help="Limit number of results")
def dlq_list(limit: Optional[int]):
    """List jobs in Dead Letter Queue."""
    storage = get_storage()
    dlq_manager = DLQManager(storage)
    dlq_manager.list_jobs(limit)


@dlq.command()
@click.argument("job_id", type=str)
def retry(job_id: str):
    """Retry a job from Dead Letter Queue."""
    storage = get_storage()
    dlq_manager = DLQManager(storage)
    dlq_manager.retry_job(job_id)


@cli.group()
def config():
    """Manage configuration."""
    pass


@config.command()
@click.argument("key", type=str)
def get(key: str):
    """Get configuration value."""
    config_manager = get_config()
    value = config_manager.get(key)
    if value is not None:
        click.echo(f"{key} = {value}")
    else:
        click.echo(f"Configuration key '{key}' not found.")


@config.command()
@click.argument("key", type=str)
@click.argument("value", type=str)
def set(key: str, value: str):
    """Set configuration value."""
    config_manager = get_config()
    
    # Try to parse value as appropriate type
    try:
        # Try integer
        if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
            parsed_value = int(value)
        # Try float
        elif "." in value:
            parsed_value = float(value)
        # Try boolean
        elif value.lower() in ("true", "false"):
            parsed_value = value.lower() == "true"
        else:
            parsed_value = value
    except:
        parsed_value = value
    
    config_manager.set(key, parsed_value)
    click.echo(f"Set {key} = {parsed_value}")


if __name__ == "__main__":
    cli()

