#!/usr/bin/env python3
"""Test script to demonstrate queuectl functionality."""

import sys
import time
from cli import get_storage, get_config
from job import Job, JobState
from worker import get_worker_manager
import threading

def main():
    print("=" * 60)
    print("queuectl Test Run")
    print("=" * 60)
    
    storage = get_storage()
    config = get_config()
    
    # Enqueue some jobs
    print("\n1. Enqueuing test jobs...")
    job1 = Job(command="echo Hello World", max_retries=3)
    job2 = Job(command="echo This is test job 2", max_retries=3)
    job3 = Job(command="echo Test job 3", max_retries=3)
    
    storage.add_job(job1)
    storage.add_job(job2)
    storage.add_job(job3)
    
    print(f"   [+] Enqueued job {job1.id[:8]}...: {job1.command}")
    print(f"   [+] Enqueued job {job2.id[:8]}...: {job2.command}")
    print(f"   [+] Enqueued job {job3.id[:8]}...: {job3.command}")
    
    # Show status
    print("\n2. Queue status:")
    stats = storage.get_stats()
    for state, count in stats.items():
        if count > 0:
            print(f"   {state}: {count}")
    
    # List jobs
    print("\n3. Listing all jobs:")
    jobs = storage.list_jobs()
    for job in jobs[:5]:  # Show first 5
        print(f"   - {job['id'][:8]}... | {job['state']} | {job['command']}")
    
    # Start a worker in the background
    print("\n4. Starting worker to process jobs...")
    manager = get_worker_manager(storage, config)
    manager.start_workers(1)
    
    # Wait a bit for jobs to process
    print("   Waiting for jobs to process...")
    for i in range(10):
        time.sleep(0.5)
        stats = storage.get_stats()
        pending = stats.get('pending', 0)
        processing = stats.get('processing', 0)
        completed = stats.get('completed', 0)
        if pending == 0 and processing == 0:
            break
        if i % 2 == 0:
            print(f"   Status: pending={pending}, processing={processing}, completed={completed}")
    
    # Show final status
    print("\n5. Final queue status:")
    stats = storage.get_stats()
    for state, count in stats.items():
        if count > 0:
            print(f"   {state}: {count}")
    
    # Stop workers
    print("\n6. Stopping workers...")
    manager.stop_workers()
    
    # List completed jobs
    print("\n7. Completed jobs:")
    completed_jobs = storage.list_jobs(JobState.COMPLETED)
    for job in completed_jobs:
        print(f"   - {job['id'][:8]}... | {job['command']}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

