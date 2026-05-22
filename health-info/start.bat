@echo off
echo Starting CalorIQ...

:: Read GROQ_API_KEY from backend\.env
for /f "tokens=1,* delims==" %%A in ('findstr "GROQ_API_KEY" backend\.env') do (
    if "%%A"=="GROQ_API_KEY" set GROQ_API_KEY=%%B
)

:: Start backend
start "CalorIQ Backend" cmd /k "cd backend && venv\Scripts\uvicorn main:app --port 8000"

:: Start frontend
start "CalorIQ Frontend" cmd /k "cd frontend && node_modules\.bin\vite"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Opening browser...
timeout /t 4 >nul
start http://localhost:5173
