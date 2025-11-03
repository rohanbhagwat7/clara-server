@echo off
REM Clara Infrastructure - Quick Setup Script (Windows)

echo ========================================
echo Clara Infrastructure Setup
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo Creating .env file from .env.docker...
    copy .env.docker .env
    echo ✓ .env file created
    echo.
) else (
    echo ✓ .env file already exists
    echo.
)

echo Starting Clara infrastructure services...
echo.
docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start services!
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✓ Setup Complete!
echo ========================================
echo.
echo Services started:
docker-compose ps

echo.
echo Connection URLs for clara-agent/.env.local:
echo.
echo   REDIS_URL=redis://localhost:6379
echo   DATABASE_URL=postgresql://clara:clara_dev_password@localhost:5432/clara
echo   TIMESCALE_URL=postgresql://clara:clara_analytics_password@localhost:5433/clara_analytics
echo.
echo Storage backends:
echo   CACHE_STORAGE_BACKEND=redis
echo   ANALYTICS_STORAGE_BACKEND=timescale
echo   PREFERENCES_STORAGE_BACKEND=database
echo.
echo ========================================
echo.
echo Useful commands:
echo   docker-compose ps          - Check status
echo   docker-compose logs -f     - View logs
echo   docker-compose stop        - Stop services
echo   docker-compose restart     - Restart services
echo.

pause
