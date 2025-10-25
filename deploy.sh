#!/bin/bash

# Sandesh Production Deployment Script
# This script handles the complete deployment process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log_success "Docker is running"
}

# Check environment variables
check_env() {
    log_info "Checking environment variables..."
    
    if [ -z "$POSTGRES_PASSWORD" ]; then
        log_warning "POSTGRES_PASSWORD not set, using default"
        export POSTGRES_PASSWORD="secure_password_123"
    fi
    
    if [ -z "$AWS_ACCESS_KEY_ID" ]; then
        log_error "AWS_ACCESS_KEY_ID is required"
        exit 1
    fi
    
    if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        log_error "AWS_SECRET_ACCESS_KEY is required"
        exit 1
    fi
    
    if [ -z "$SES_SENDER_EMAIL" ]; then
        log_error "SES_SENDER_EMAIL is required"
        exit 1
    fi
    
    # Set defaults
    export AWS_REGION=${AWS_REGION:-"ap-south-1"}
    export REACT_APP_API_URL=${REACT_APP_API_URL:-"http://localhost:8000"}
    
    log_success "Environment variables validated"
}

# Clean up previous deployment
cleanup() {
    log_info "Cleaning up previous deployment..."
    docker-compose down --remove-orphans 2>/dev/null || true
    docker system prune -f > /dev/null 2>&1 || true
    log_success "Cleanup completed"
}

# Build and start services
deploy() {
    log_info "Building and starting services..."
    
    # Build images
    log_info "Building Docker images..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
    
    # Start services
    log_info "Starting services..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    log_success "Services started successfully"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    # Wait for database
    log_info "Waiting for database..."
    timeout 60 bash -c 'until docker-compose exec postgres pg_isready -U postgres; do sleep 2; done'
    
    # Wait for backend
    log_info "Waiting for backend..."
    timeout 60 bash -c 'until curl -f http://localhost:8000/health > /dev/null 2>&1; do sleep 2; done'
    
    # Wait for frontend
    log_info "Waiting for frontend..."
    timeout 60 bash -c 'until curl -f http://localhost:3000 > /dev/null 2>&1; do sleep 2; done'
    
    log_success "All services are healthy"
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    echo ""
    docker-compose ps
    echo ""
    log_info "Service URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8000"
    echo "  Database: localhost:5433"
    echo ""
    log_info "Health Checks:"
    echo "  Frontend: curl http://localhost:3000"
    echo "  Backend:  curl http://localhost:8000/health"
    echo ""
}

# Main deployment function
main() {
    log_info "Starting Sandesh deployment..."
    echo ""
    
    check_docker
    check_env
    cleanup
    deploy
    wait_for_services
    show_status
    
    log_success "🎉 Deployment completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "1. Access the application at http://localhost:3000"
    echo "2. Check logs with: docker-compose logs -f"
    echo "3. Monitor services with: docker-compose ps"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    "clean")
        cleanup
        log_success "Cleanup completed"
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "restart")
        log_info "Restarting services..."
        docker-compose restart
        log_success "Services restarted"
        ;;
    "stop")
        log_info "Stopping services..."
        docker-compose down
        log_success "Services stopped"
        ;;
    "help"|"-h"|"--help")
        echo "Sandesh Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no args)  - Full deployment"
        echo "  clean      - Clean up containers and images"
        echo "  status      - Show deployment status"
        echo "  logs        - Show service logs"
        echo "  restart     - Restart all services"
        echo "  stop        - Stop all services"
        echo "  help        - Show this help"
        echo ""
        echo "Environment Variables:"
        echo "  POSTGRES_PASSWORD     - Database password (default: secure_password_123)"
        echo "  AWS_ACCESS_KEY_ID     - AWS access key (required)"
        echo "  AWS_SECRET_ACCESS_KEY - AWS secret key (required)"
        echo "  SES_SENDER_EMAIL      - Verified SES email (required)"
        echo "  AWS_REGION           - AWS region (default: ap-south-1)"
        echo "  REACT_APP_API_URL    - Frontend API URL (default: http://localhost:8000)"
        ;;
    *)
        main
        ;;
esac
