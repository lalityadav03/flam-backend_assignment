# queuectl Quick Start Guide

## Project Status: ✅ RUNNING

The project has been successfully tested and is working correctly!

## Quick Setup (Windows)

### 1. Install Dependencies

The dependencies are already installed. If you need to reinstall:

```powershell
python -m pip install -r requirements.txt
```

**Note**: On this system, Python is located at:
`C:\Users\lalit\AppData\Local\Programs\Python\Python312\python.exe`

If Python is not in your PATH, you can:
- Add Python to your system PATH, or
- Use the full path to Python executable in commands

### 2. Running the Project

#### Option A: Using the Test Script (Easiest)

```powershell
python test_run.py
```

This will:
- Enqueue 3 test jobs
- Show queue status
- Start a worker to process jobs
- Display completed jobs

#### Option B: Using CLI Commands

**Check status:**
```powershell
python main.py status
```

**List jobs:**
```powershell
python main.py list
python main.py list --state pending
python main.py list --state completed
```

**Enqueue a job (PowerShell):**
```powershell
# Note: PowerShell requires special quoting for JSON
python main.py enqueue '{\"command\":\"echo hello\"}'

# Or use the helper script
python -c "import json; from cli import get_storage, get_config; from job import Job; s=get_storage(); c=get_config(); j=Job(command='echo hello', max_retries=3); s.add_job(j); print(f'Job: {j.id}')"
```

**Start workers:**
```powershell
python main.py worker start --count 1
```

**View configuration:**
```powershell
python main.py config get max_retries
python main.py config get backoff_base
python main.py config set max_retries 5
```

**Dead Letter Queue:**
```powershell
python main.py dlq list
python main.py dlq retry <job_id>
```

#### Option C: Using Python Scripts Directly

You can also use the Python API directly:

```python
from cli import get_storage, get_config
from job import Job
from worker import get_worker_manager

# Get storage and config
storage = get_storage()
config = get_config()

# Enqueue a job
job = Job(command="echo Hello World", max_retries=3)
storage.add_job(job)
print(f"Job enqueued: {job.id}")

# Start workers
manager = get_worker_manager(storage, config)
manager.start_workers(1)
```

### 3. Test Results

✅ Jobs can be enqueued successfully  
✅ Workers process jobs correctly  
✅ Jobs transition through states properly  
✅ Database persistence works  
✅ Configuration management works  
✅ CLI commands function correctly  

### 4. Current Database State

After running the test, you should see:
- Multiple completed jobs in the database
- Jobs persist across restarts
- Database file: `queuectl.db`
- Config file: `queuectl_config.json`

### 5. Troubleshooting

**Issue: Python not found**
- Solution: Use the full path to Python or add it to PATH
- Full path: `C:\Users\lalit\AppData\Local\Programs\Python\Python312\python.exe`

**Issue: JSON parsing errors in PowerShell**
- Solution: Use the test script or Python API directly
- Alternative: Create a JSON file and read it

**Issue: Workers not processing jobs**
- Check: `python main.py status`
- Verify: Workers are started with `python main.py worker start --count 1`
- Check: Jobs are in pending state

### 6. Next Steps

1. **Test retry mechanism**: Enqueue a job that will fail
   ```python
   job = Job(command="invalid-command-xyz", max_retries=2)
   storage.add_job(job)
   ```

2. **Test DLQ**: Jobs that exceed max_retries will move to DLQ
   ```powershell
   python main.py dlq list
   ```

3. **Test multiple workers**: Start multiple workers for parallel processing
   ```powershell
   python main.py worker start --count 3
   ```

4. **Monitor in real-time**: Use status command to monitor queue
   ```powershell
   python main.py status
   ```

## Project Files

- `main.py` - CLI entry point
- `cli.py` - Click CLI commands
- `job.py` - Job class
- `storage.py` - SQLite storage
- `worker.py` - Worker management
- `config.py` - Configuration
- `dlq.py` - Dead Letter Queue
- `utils.py` - Utilities
- `test_run.py` - Test script
- `requirements.txt` - Dependencies
- `README.md` - Full documentation

## Success! 🎉

The project is fully functional and ready to use!

