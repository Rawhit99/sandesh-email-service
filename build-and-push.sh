#!/bin/bash

# Sandesh Email Service - Docker Image Builder
# This script builds and pushes Docker images to Docker Hub

set -e

# Configuration
DOCKERHUB_USERNAME=""
BACKEND_IMAGE_NAME="sandesh-email-backend"
FRONTEND_IMAGE_NAME="sandesh-email-frontend"
VERSION="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Sandesh Email Service - Docker Image Builder${NC}"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Get Docker Hub username
if [ -z "$DOCKERHUB_USERNAME" ]; then
    echo -e "${YELLOW}📝 Please enter your Docker Hub username:${NC}"
    read -p "Docker Hub Username: " DOCKERHUB_USERNAME
    
    if [ -z "$DOCKERHUB_USERNAME" ]; then
        echo -e "${RED}❌ Docker Hub username is required.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Using Docker Hub username: $DOCKERHUB_USERNAME${NC}"

# Login to Docker Hub
echo -e "${YELLOW}🔐 Logging into Docker Hub...${NC}"
docker login

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to login to Docker Hub.${NC}"
    exit 1
fi

# Build backend image
echo -e "${YELLOW}🔨 Building backend image...${NC}"
docker build -t $DOCKERHUB_USERNAME/$BACKEND_IMAGE_NAME:$VERSION ./backend

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to build backend image.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend image built successfully${NC}"

# Build frontend image
echo -e "${YELLOW}🔨 Building frontend image...${NC}"
docker build -t $DOCKERHUB_USERNAME/$FRONTEND_IMAGE_NAME:$VERSION ./frontend

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to build frontend image.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend image built successfully${NC}"

# Push backend image
echo -e "${YELLOW}📤 Pushing backend image to Docker Hub...${NC}"
docker push $DOCKERHUB_USERNAME/$BACKEND_IMAGE_NAME:$VERSION

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to push backend image.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend image pushed successfully${NC}"

# Push frontend image
echo -e "${YELLOW}📤 Pushing frontend image to Docker Hub...${NC}"
docker push $DOCKERHUB_USERNAME/$FRONTEND_IMAGE_NAME:$VERSION

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to push frontend image.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend image pushed successfully${NC}"

# Update public docker-compose file
echo -e "${YELLOW}📝 Updating public docker-compose file...${NC}"
sed -i.bak "s/YOUR_DOCKERHUB_USERNAME/$DOCKERHUB_USERNAME/g" docker-compose.public.yml

echo -e "${GREEN}✅ Public docker-compose file updated${NC}"

# Create .env.example
echo -e "${YELLOW}📝 Creating .env.example file...${NC}"
cat > .env.example << EOF
# Sandesh Email Service - Environment Configuration
# Copy this file to .env and update with your values

# ============================================
# AWS SES Configuration (Required for SES)
# ============================================
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-south-1
SES_SENDER_EMAIL=your-verified-email@domain.com
SES_CONFIGURATION_SET=

# ============================================
# SMTP Configuration (Alternative to SES)
# ============================================
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_SENDER_EMAIL=your-email@gmail.com

# ============================================
# Frontend Configuration
# ============================================
REACT_APP_API_URL=http://localhost:8000

# ============================================
# API Security
# ============================================
API_KEYS=your-secure-api-key
EOF

echo -e "${GREEN}✅ .env.example file created${NC}"

echo ""
echo -e "${GREEN}🎉 All done! Your Docker images are now available publicly.${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Share these files with users:"
echo "   - docker-compose.public.yml (rename to docker-compose.yml)"
echo "   - .env.example"
echo "   - README.public.md"
echo ""
echo "2. Users can now run:"
echo "   - Copy .env.example to .env and configure"
echo "   - docker compose up -d"
echo ""
echo -e "${GREEN}🔗 Your images are available at:${NC}"
echo "   - $DOCKERHUB_USERNAME/$BACKEND_IMAGE_NAME:$VERSION"
echo "   - $DOCKERHUB_USERNAME/$FRONTEND_IMAGE_NAME:$VERSION"
echo ""
echo -e "${YELLOW}⚠️  Remember to:${NC}"
echo "   - Keep your source code private"
echo "   - Monitor Docker Hub usage (rate limits apply)"
echo "   - Update images when you make changes"
