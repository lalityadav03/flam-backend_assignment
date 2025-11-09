@echo off
REM Helper script to enqueue jobs on Windows
REM Usage: enqueue_job.bat "command here"

if "%~1"=="" (
    echo Usage: enqueue_job.bat "command here"
    echo Example: enqueue_job.bat "echo hello"
    exit /b 1
)

set PYTHON_EXE=C:\Users\lalit\AppData\Local\Programs\Python\Python312\python.exe

echo Enqueuing job: %~1
%PYTHON_EXE% -c "import json, sys; from cli import get_storage, get_config; from job import Job; storage = get_storage(); config = get_config(); job = Job(command=sys.argv[1], max_retries=config.get('max_retries', 3)); storage.add_job(job); print(f'Job enqueued: {job.id}'); print(f'Command: {job.command}')" %~1

