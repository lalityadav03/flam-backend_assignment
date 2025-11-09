# Setup and run script for queuectl (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "queuectl Setup and Run" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
$pythonCmd = $null
$pythonCommands = @("python", "python3", "py")

foreach ($cmd in $pythonCommands) {
    try {
        $result = Get-Command $cmd -ErrorAction Stop
        $pythonCmd = $cmd
        break
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Host "Python is not found in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.7+ and add it to your PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "You can download Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Python found: $pythonCmd" -ForegroundColor Green
& $pythonCmd --version
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& $pythonCmd -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run:" -ForegroundColor Cyan
Write-Host "  $pythonCmd main.py --help" -ForegroundColor White
Write-Host "  $pythonCmd main.py enqueue '{\"command\":\"echo hello\"}'" -ForegroundColor White
Write-Host "  $pythonCmd main.py worker start --count 1" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"

