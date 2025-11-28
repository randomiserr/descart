@echo off
echo Starting Czech Political Advisor...
echo.
echo [1/2] Starting FastAPI Backend...
start "Backend API" cmd /k "python api.py"
timeout /t 3 /nobreak > nul

echo [2/2] Starting React Frontend...
start "React Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo Both servers are starting!
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo React App:   http://localhost:3000
echo.
echo Press any key to open the app in your browser...
pause > nul
start http://localhost:3000
