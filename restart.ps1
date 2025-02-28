# PowerShell script to restart the Flask server
Write-Host "=== X Bot Checker Server Restart Utility ===" -ForegroundColor Green

# Kill any existing Python processes running api.py
Write-Host "Stopping any existing Flask servers..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*api.py*" }
if ($pythonProcesses) {
    $pythonProcesses | ForEach-Object { 
        Write-Host "Stopping process with ID: $($_.Id)" -ForegroundColor Yellow
        Stop-Process -Id $_.Id -Force 
    }
    Write-Host "Existing Flask servers stopped." -ForegroundColor Green
} else {
    Write-Host "No existing Flask servers found." -ForegroundColor Yellow
}

# Clear cache directories
Write-Host "Clearing cache directories..." -ForegroundColor Yellow
$cacheDir = Join-Path $PSScriptRoot "cache"
$pycacheDir = Join-Path $PSScriptRoot "__pycache__"

if (Test-Path $cacheDir) {
    Write-Host "Clearing cache directory: $cacheDir" -ForegroundColor Yellow
    Get-ChildItem -Path $cacheDir -Recurse | Remove-Item -Force -Recurse
    Write-Host "Cache directory cleared." -ForegroundColor Green
} else {
    Write-Host "No cache directory found." -ForegroundColor Yellow
}

if (Test-Path $pycacheDir) {
    Write-Host "Clearing __pycache__ directory: $pycacheDir" -ForegroundColor Yellow
    Remove-Item -Path $pycacheDir -Force -Recurse
    Write-Host "__pycache__ directory cleared." -ForegroundColor Green
} else {
    Write-Host "No __pycache__ directory found." -ForegroundColor Yellow
}

# Start the Flask server
Write-Host "Starting Flask server..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "api.py" -NoNewWindow

Write-Host "`nServer has been restarted with a clean cache." -ForegroundColor Green
Write-Host "Please also clear your browser cache or use incognito mode to see the changes." -ForegroundColor Cyan
Write-Host "The server is now running at http://127.0.0.1:5000" -ForegroundColor Cyan 