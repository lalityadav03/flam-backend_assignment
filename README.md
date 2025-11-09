# queuectl

A CLI-based background job queue system with support for job enqueuing, multiple workers, automatic retries with exponential backoff, and a Dead Letter Queue (DLQ).

## Features

- **Job Queue Management**: Enqueue and manage background jobs
- **Multiple Workers**: Run multiple worker threads to process jobs in parallel
- **Automatic Retries**: Jobs automatically retry on failure with exponential backoff
- **Dead Letter Queue**: Failed jobs after max retries are moved to DLQ
- **Persistent Storage**: SQLite database for job persistence across restarts
- **State Management**: Jobs transition through states: `pending` → `processing` → `completed`/`failed` → `dead`
- **Configuration Management**: Configurable retry limits and backoff settings
- **CLI Interface**: User-friendly command-line interface using Click

## Architecture

### Components

- **Job (`job.py`)**: Job data class with state management
- **Storage (`storage.py`)**: SQLite-based persistence layer
- **Worker (`worker.py`)**: Worker threads for job processing
- **Config (`config.py`)**: Configuration management
- **DLQ (`dlq.py`)**: Dead Letter Queue management
- **CLI (`cli.py`)**: Command-line interface
- **Utils (`utils.py`)**: Utility functions

### Job States

- `pending`: Job is waiting to be processed
- `processing`: Job is currently being executed
- `completed`: Job completed successfully
- `failed`: Job failed but can be retried
- `dead`: Job exceeded max retries and moved to DLQ

### Database Schema

**jobs table:**
- `id`: Unique job identifier
- `command`: Shell command to execute
- `state`: Current job state
- `attempts`: Number of execution attempts
- `max_retries`: Maximum retry limit
- `created_at`: Job creation timestamp
- `updated_at`: Last update timestamp
- `error_message`: Error message if job failed

**dlq table:**
- `id`: Job identifier
- `command`: Shell command
- `attempts`: Number of attempts made
- `max_retries`: Maximum retry limit
- `created_at`: Original creation timestamp
- `moved_at`: Timestamp when moved to DLQ
- `error_message`: Error message

## Installation

1. Clone or download the project
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Enqueue a Job

Enqueue a new job with a JSON string containing the command:

```bash
python main.py enqueue '{"command":"echo hello"}'
python main.py enqueue '{"command":"sleep 5"}'
python main.py enqueue '{"command":"python script.py"}' --max-retries 5
```

### Start Workers

Start worker threads to process jobs:

```bash
# Start 1 worker (default)
python main.py worker start

# Start multiple workers
python main.py worker start --count 3
```

Workers run in the foreground. Press `Ctrl+C` to stop them gracefully.

### Stop Workers

```bash
python main.py worker stop
```

### List Jobs

List all jobs or filter by state:

```bash
# List all jobs
python main.py list

# List pending jobs
python main.py list --state pending

# List completed jobs
python main.py list --state completed

# List with limit
python main.py list --limit 10
```

### Check Status

Get queue statistics:

```bash
python main.py status
```

### Dead Letter Queue

List jobs in DLQ:

```bash
python main.py dlq list
```

Retry a job from DLQ:

```bash
python main.py dlq retry <job_id>
```

### Configuration

Get configuration value:

```bash
python main.py config get max_retries
python main.py config get backoff_base
```

Set configuration value:

```bash
python main.py config set max_retries 5
python main.py config set backoff_base 3
```

## Examples

### Example 1: Basic Job Processing

```bash
# Enqueue a job
python main.py enqueue '{"command":"echo Hello World"}'

# Start a worker
python main.py worker start --count 1
```

### Example 2: Jobs with Retries

```bash
# Enqueue a job that will fail
python main.py enqueue '{"command":"exit 1"}' --max-retries 3

# Set backoff base
python main.py config set backoff_base 2

# Start worker
python main.py worker start --count 1
```

The job will retry up to 3 times with exponential backoff delays (2, 4, 8 seconds).

### Example 3: Dead Letter Queue

```bash
# Enqueue a failing job
python main.py enqueue '{"command":"invalid-command-xyz"}' --max-retries 2

# Start worker (job will fail and move to DLQ)
python main.py worker start --count 1

# Check DLQ
python main.py dlq list

# Retry a job from DLQ
python main.py dlq retry <job_id>
```

### Example 4: Multiple Workers

```bash
# Enqueue multiple jobs
python main.py enqueue '{"command":"sleep 2"}'
python main.py enqueue '{"command":"sleep 2"}'
python main.py enqueue '{"command":"sleep 2"}'

# Start 3 workers to process in parallel
python main.py worker start --count 3
```

### Example 5: Monitoring

```bash
# Check queue status
python main.py status

# List pending jobs
python main.py list --state pending

# List processing jobs
python main.py list --state processing

# List failed jobs
python main.py list --state failed
```

## Configuration

Default configuration values:

- `max_retries`: 3
- `backoff_base`: 2

The backoff delay is calculated as: `delay = backoff_base ^ attempts`

For example, with `backoff_base = 2`:
- Attempt 1: 2 seconds
- Attempt 2: 4 seconds
- Attempt 3: 8 seconds

Configuration is stored in `queuectl_config.json`.

## Database

Jobs are stored in `queuectl.db` (SQLite database). The database persists across restarts, so jobs are preserved.

To reset the database, delete `queuectl.db`:

```bash
rm queuectl.db
```

## Error Handling

- Jobs that fail are automatically retried with exponential backoff
- After max retries, jobs are moved to the Dead Letter Queue
- Jobs in DLQ can be manually retried using `dlq retry`
- Jobs have a 5-minute timeout to prevent hanging

## State Transitions

1. **Enqueue**: Job created in `pending` state
2. **Worker picks up**: Job moves to `processing` state
3. **Success**: Job moves to `completed` state
4. **Failure**: Job moves to `failed` state
5. **Retry**: Job moves back to `pending` state (after backoff delay)
6. **Max retries exceeded**: Job moves to `dead` state and is moved to DLQ

## Thread Safety

- Worker threads are thread-safe
- Database operations use connection management for thread safety
- Multiple workers can process jobs concurrently without conflicts

## Limitations

- Jobs are processed in FIFO order (by creation time)
- Command timeout is fixed at 5 minutes
- Workers run in the same process (not distributed)
- SQLite may have concurrency limitations with many workers

## Troubleshooting

### Workers not processing jobs

- Check if workers are running: `python main.py status`
- Check job state: `python main.py list --state pending`
- Verify workers are started: `python main.py worker start --count 1`

### Jobs stuck in processing

- Jobs may have timed out or crashed
- Check database directly or restart workers
- Consider increasing timeout in `worker.py`

### Database locked

- SQLite may have concurrency issues with many workers
- Reduce worker count or ensure proper cleanup

## License

This project is provided as-is for educational and development purposes.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

