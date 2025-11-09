#!/usr/bin/env python3
"""Demo script to test queuectl functionality."""

import sys
import time
import subprocess
from storage import JobStorage
from config import ConfigManager
from job import Job, JobState

def main():
    print("=" * 60)
    print("queuectl Demo")
    print("=" * 60)
    
    # Initialize storage and config
    print("\n1. Initializing storage and config...")
    storage = JobStorage()
    config = ConfigManager()
    print("   ✓ Storage initialized")
    print("   ✓ Config initialized")
    
    # Show current config
    print(f"\n2. Current configuration:")
    print(f"   max_retries: {config.get('max_retries')}")
    print(f"   backoff_base: {config.get('backoff_base')}")
    
    # Add some test jobs
    print("\n3. Adding test jobs...")
    job1 = Job(command="echo 'Hello from job 1'", max_retries=3)
    job2 = Job(command="echo 'Hello from job 2'", max_retries=3)
    job3 = Job(command="exit 1", max_retries=2)  # This will fail
    
    storage.add_job(job1)
    storage.add_job(job2)
    storage.add_job(job3)
    
    print(f"   ✓ Added job {job1.id}: {job1.command}")
    print(f"   ✓ Added job {job2.id}: {job2.command}")
    print(f"   ✓ Added job {job3.id}: {job3.command} (will fail)")
    
    # Show stats
    print("\n4. Queue statistics:")
    stats = storage.get_stats()
    for state, count in stats.items():
        if count > 0:
            print(f"   {state}: {count}")
    
    # List pending jobs
    print("\n5. Pending jobs:")
    pending_jobs = storage.list_jobs(JobState.PENDING)
    for job_dict in pending_jobs:
        print(f"   - {job_dict['id'][:8]}...: {job_dict['command']}")
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)
    print("\nTo run the full CLI:")
    print("  python main.py enqueue '{\"command\":\"echo hello\"}'")
    print("  python main.py worker start --count 1")
    print("  python main.py status")
    print("  python main.py list")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

