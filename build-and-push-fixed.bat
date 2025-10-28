@echo off
REM Sandesh Email Service - Docker Image Builder (Windows) - Fixed Version
setlocal enabledelayedexpansion

REM Configuration
set BACKEND_IMAGE_NAME=sandesh-email-backend
set FRONTEND_IMAGE_NAME=sandesh-email-frontend
set VERSION=latest

echo 🚀 Sandesh Email Service - Docker Image Builder
echo ==================================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)

REM Get Docker Hub username
echo 📝 Please enter your Docker Hub username:
set /p DOCKERHUB_USERNAME="Docker Hub Username: "

if "!DOCKERHUB_USERNAME!"=="" (
    echo ❌ Docker Hub username is required.
    pause
    exit /b 1
)

echo ✅ Using Docker Hub username: !DOCKERHUB_USERNAME!

REM Login to Docker Hub
echo 🔐 Logging into Docker Hub...
docker login
if errorlevel 1 (
    echo ❌ Failed to login to Docker Hub.
    pause
    exit /b 1
)

REM Build backend image
echo 🔨 Building backend image...
docker build -t !DOCKERHUB_USERNAME!/!BACKEND_IMAGE_NAME!:!VERSION! ./backend
if errorlevel 1 (
    echo ❌ Failed to build backend image.
    pause
    exit /b 1
)
echo ✅ Backend image built successfully

REM Build frontend image
echo 🔨 Building frontend image...
docker build -t !DOCKERHUB_USERNAME!/!FRONTEND_IMAGE_NAME!:!VERSION! ./frontend
if errorlevel 1 (
    echo ❌ Failed to build frontend image.
    pause
    exit /b 1
)
echo ✅ Frontend image built successfully

REM Push backend image
echo 📤 Pushing backend image to Docker Hub...
docker push !DOCKERHUB_USERNAME!/!BACKEND_IMAGE_NAME!:!VERSION!
if errorlevel 1 (
    echo ❌ Failed to push backend image.
    pause
    exit /b 1
)
echo ✅ Backend image pushed successfully

REM Push frontend image
echo 📤 Pushing frontend image to Docker Hub...
docker push !DOCKERHUB_USERNAME!/!FRONTEND_IMAGE_NAME!:!VERSION!
if errorlevel 1 (
    echo ❌ Failed to push frontend image.
    pause
    exit /b 1
)
echo ✅ Frontend image pushed successfully

REM Update public docker-compose file
echo 📝 Updating public docker-compose file...
powershell -Command "(Get-Content docker-compose.public.yml) -replace 'YOUR_DOCKERHUB_USERNAME', '!DOCKERHUB_USERNAME!' | Set-Content docker-compose.public.yml"
echo ✅ Public docker-compose file updated

echo.
echo 🎉 All done! Your Docker images are now available publicly.
echo.
echo 📋 Next steps:
echo 1. Share these files with users:
echo    - docker-compose.public.yml ^(rename to docker-compose.yml^)
echo    - .env.example
echo    - README.public.md
echo.
echo 2. Users can now run:
echo    - Copy .env.example to .env and configure
echo    - docker compose up -d
echo.
echo 🔗 Your images are available at:
echo    - !DOCKERHUB_USERNAME!/!BACKEND_IMAGE_NAME!:!VERSION!
echo    - !DOCKERHUB_USERNAME!/!FRONTEND_IMAGE_NAME!:!VERSION!

pause
