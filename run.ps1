# Start Backend
Write-Host "Starting FastAPI Backend on port 8000..." -ForegroundColor Cyan
Start-Process powershell -WorkingDirectory $PSScriptRoot -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

# Start Frontend
Write-Host "Starting React Frontend on port 5173..." -ForegroundColor Cyan
Start-Process powershell -WorkingDirectory "$PSScriptRoot\react-app" -ArgumentList "-NoExit", "-Command", "cmd.exe /c `"npm run dev`""

Write-Host "Both servers are running!" -ForegroundColor Green
Write-Host "Backend API: http://localhost:8000/docs"
Write-Host "Dashboard UI: http://localhost:5173"
Write-Host "Press Ctrl+C to stop (you may need to manually close the node and python processes in Task Manager)."
