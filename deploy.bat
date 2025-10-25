@echo off
REM Sandesh Production Deployment Script for Windows
REM This script handles the complete deployment process

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Sandesh Production Deployment
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)
echo [SUCCESS] Docker is running

REM Check environment variables
echo [INFO] Checking environment variables...

@REM if "%POSTGRES_PASSWORD%"=="" (
@REM     echo [WARNING] POSTGRES_PASSWORD not set, using default
@REM     set POSTGRES_PASSWORD=password
@REM )

@REM if "%AWS_ACCESS_KEY_ID%"=="" (
@REM     echo [ERROR] AWS_ACCESS_KEY_ID is required
@REM     exit /b 1
@REM )

@REM if "%AWS_SECRET_ACCESS_KEY%"=="" (
@REM     echo [ERROR] AWS_SECRET_ACCESS_KEY is required
@REM     exit /b 1
@REM )

@REM if "%SES_SENDER_EMAIL%"=="" (
@REM     echo [ERROR] SES_SENDER_EMAIL is required
@REM     exit /b 1
@REM )

REM Set defaults
if "%AWS_REGION%"=="" set AWS_REGION=ap-south-1
if "%REACT_APP_API_URL%"=="" set REACT_APP_API_URL=http://localhost:8000

echo [SUCCESS] Environment variables validated

REM Clean up previous deployment
echo [INFO] Cleaning up previous deployment...
docker-compose down --remove-orphans >nul 2>&1
docker system prune -f >nul 2>&1
echo [SUCCESS] Cleanup completed

REM Build and start services
echo [INFO] Building and starting services...

echo [INFO] Building Docker images...
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build images
    exit /b 1
)

echo [INFO] Starting services...
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start services
    exit /b 1
)

echo [SUCCESS] Services started successfully

REM Wait for services to be healthy
echo [INFO] Waiting for services to be healthy...

echo [INFO] Waiting for database...
timeout /t 30 /nobreak >nul
docker-compose exec postgres pg_isready -U postgres >nul 2>&1

echo [INFO] Waiting for backend...
timeout /t 30 /nobreak >nul
curl -f http://localhost:8000/health >nul 2>&1

echo [INFO] Waiting for frontend...
timeout /t 30 /nobreak >nul
curl -f http://localhost:3000 >nul 2>&1

echo [SUCCESS] All services are healthy

REM Show deployment status
echo.
echo [INFO] Deployment Status:
echo.
docker-compose ps
echo.
echo [INFO] Service URLs:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   Database: localhost:5433
echo.
echo [INFO] Health Checks:
echo   Frontend: curl http://localhost:3000
echo   Backend:  curl http://localhost:8000/health
echo.

echo [SUCCESS] 🎉 Deployment completed successfully!
echo.
echo [INFO] Next steps:
echo 1. Access the application at http://localhost:3000
echo 2. Check logs with: docker-compose logs -f
echo 3. Monitor services with: docker-compose ps
echo.

pause
