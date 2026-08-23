@echo off
echo ================================
echo   NEXUS - Product Intelligence
echo ================================
echo.

echo [1/2] Starting FastAPI backend on port 8000...
start /min cmd /c "cd /d C:\Hackathon\Unilog && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo [2/2] Starting React frontend on port 5173...
start /min cmd /c "cd /d C:\Hackathon\Unilog\frontend && node node_modules\vite\bin\vite.js --host"

echo.
echo Waiting for servers...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   NEXUS is running!
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo ========================================
echo.
pause
