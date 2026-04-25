@echo off
REM Quick setup script for Windows
REM MTL Project - Ollama Integration

echo.
echo ===============================================
echo    MTL Project - Ollama Integration Setup (Windows)
echo ===============================================
echo.

REM Check Python
echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+
    exit /b 1
)

REM Install dependencies
echo.
echo Installing Python dependencies...
pip install -r requirements.txt

REM Check Ollama
echo.
echo Checking Ollama installation...
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Ollama not found. Please install from https://ollama.ai
    echo Then run: ollama pull llama2
    exit /b 1
)

echo Ollama is installed:
ollama --version

REM Create .env if needed
echo.
echo Checking .env configuration...
if not exist ".env" (
    echo Creating .env file...
    (
        echo AWS_ACCESS_KEY=your_key_here
        echo AWS_SECRET_KEY=your_secret_here
        echo OLLAMA_BASE_URL=http://localhost:11434
        echo OLLAMA_MODEL=llama2
        echo OLLAMA_ENABLED=true
    ) > .env
    echo .env created - update with your AWS credentials
) else (
    echo .env already exists
)

echo.
echo ===============================================
echo    Setup Complete!
echo ===============================================
echo.
echo Next steps:
echo 1. Start Ollama: ollama serve
echo 2. In new terminal, start API: uvicorn app:app --reload
echo 3. Test: curl http://localhost:8000/ollama/status
echo.
pause
