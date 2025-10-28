# Sandesh Email Service - Public Setup
# 
# This setup allows anyone to run your email service using pre-built Docker images
# without needing access to your source code.
#
# Prerequisites:
# 1. Docker and Docker Compose installed
# 2. AWS SES credentials (or SMTP settings)
#
# Quick Start:
# 1. Copy this docker-compose.public.yml to docker-compose.yml
# 2. Update YOUR_DOCKERHUB_USERNAME with your actual Docker Hub username
# 3. Create a .env file with your configuration (see .env.example below)
# 4. Run: docker compose up -d
#
# Environment Variables (.env file):
# ============================================
# AWS SES Configuration (Required for SES)
# ============================================
# AWS_ACCESS_KEY_ID=your_aws_access_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret_key
# AWS_REGION=ap-south-1
# SES_SENDER_EMAIL=your-verified-email@domain.com
# SES_CONFIGURATION_SET=
#
# ============================================
# SMTP Configuration (Alternative to SES)
# ============================================
# EMAIL_PROVIDER=smtp
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
# SMTP_USE_TLS=true
# SMTP_USE_SSL=false
# SMTP_SENDER_EMAIL=your-email@gmail.com
#
# ============================================
# Frontend Configuration
# ============================================
# REACT_APP_API_URL=http://localhost:8000
#
# ============================================
# API Security
# ============================================
# API_KEYS=your-secure-api-key
#
# Access the application:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
#
# Default Database:
# - Host: localhost:5433
# - Database: emails
# - Username: postgres
# - Password: password
#
# To register a new user account, visit: http://localhost:3000/register
