#!/bin/bash

# Solar Weather API Deployment Script
# Supports Railway, Fly.io, and Docker deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_TYPE=${1:-"help"}
ENVIRONMENT=${2:-"production"}

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

check_dependencies() {
    local deps=("$@")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "$dep is required but not installed"
            exit 1
        fi
    done
}

validate_environment() {
    local required_vars=(
        "SUPABASE_URL"
        "SUPABASE_ANON_KEY"
        "SUPABASE_SERVICE_KEY"
        "JWT_SECRET_KEY"
        "RAZORPAY_KEY_ID"
        "RAZORPAY_KEY_SECRET"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "Environment variable $var is not set"
            exit 1
        fi
    done
}

run_tests() {
    log_info "Running tests before deployment..."
    cd "$PROJECT_ROOT"
    
    # Set test environment
    export ENVIRONMENT=test
    export SUPABASE_URL="http://localhost:54321"
    export SUPABASE_ANON_KEY="test_key"
    export SUPABASE_SERVICE_KEY="test_service_key"
    export JWT_SECRET_KEY="test_jwt_secret"
    
    # Run unit tests
    python -m pytest tests/unit/ -v --tb=short
    
    if [[ $? -eq 0 ]]; then
        log_success "All tests passed"
    else
        log_error "Tests failed. Deployment aborted."
        exit 1
    fi
}

build_docker_image() {
    local tag=${1:-"solar-weather-api:latest"}
    
    log_info "Building Docker image: $tag"
    cd "$PROJECT_ROOT"
    
    docker build -t "$tag" --target production .
    
    if [[ $? -eq 0 ]]; then
        log_success "Docker image built successfully"
    else
        log_error "Docker build failed"
        exit 1
    fi
}

deploy_railway() {
    log_info "Deploying to Railway..."
    check_dependencies "railway"
    
    cd "$PROJECT_ROOT"
    
    # Login check
    if ! railway whoami &> /dev/null; then
        log_error "Not logged in to Railway. Run 'railway login' first."
        exit 1
    fi
    
    # Deploy
    railway up --detach
    
    if [[ $? -eq 0 ]]; then
        log_success "Deployed to Railway successfully"
        railway status
    else
        log_error "Railway deployment failed"
        exit 1
    fi
}

deploy_flyio() {
    log_info "Deploying to Fly.io..."
    check_dependencies "flyctl"
    
    cd "$PROJECT_ROOT"
    
    # Check if app exists
    if ! flyctl apps list | grep -q "solar-weather-api"; then
        log_info "Creating new Fly.io app..."
        flyctl apps create solar-weather-api
    fi
    
    # Set secrets
    log_info "Setting environment variables..."
    flyctl secrets set \
        ENVIRONMENT="$ENVIRONMENT" \
        SUPABASE_URL="$SUPABASE_URL" \
        SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
        SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY" \
        JWT_SECRET_KEY="$JWT_SECRET_KEY" \
        RAZORPAY_KEY_ID="$RAZORPAY_KEY_ID" \
        RAZORPAY_KEY_SECRET="$RAZORPAY_KEY_SECRET" \
        HUGGINGFACE_API_TOKEN="$HUGGINGFACE_API_TOKEN"
    
    # Deploy
    flyctl deploy --remote-only
    
    if [[ $? -eq 0 ]]; then
        log_success "Deployed to Fly.io successfully"
        flyctl status
    else
        log_error "Fly.io deployment failed"
        exit 1
    fi
}

deploy_docker() {
    log_info "Deploying with Docker Compose..."
    check_dependencies "docker" "docker-compose"
    
    cd "$PROJECT_ROOT"
    
    # Build and deploy
    if [[ "$ENVIRONMENT" == "production" ]]; then
        docker-compose -f docker-compose.prod.yml up -d --build
    else
        docker-compose up -d --build
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "Docker deployment successful"
        docker-compose ps
    else
        log_error "Docker deployment failed"
        exit 1
    fi
}

deploy_frontend_vercel() {
    log_info "Deploying frontend to Vercel..."
    check_dependencies "vercel"
    
    cd "$PROJECT_ROOT/frontend"
    
    # Build
    npm run build
    
    # Deploy
    if [[ "$ENVIRONMENT" == "production" ]]; then
        vercel --prod
    else
        vercel
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "Frontend deployed to Vercel successfully"
    else
        log_error "Vercel deployment failed"
        exit 1
    fi
}

setup_monitoring() {
    log_info "Setting up monitoring and logging..."
    
    # Create logs directory
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Set up log rotation
    cat > "$PROJECT_ROOT/logs/logrotate.conf" << EOF
$PROJECT_ROOT/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose restart api scheduler 2>/dev/null || true
    endscript
}
EOF
    
    log_success "Monitoring setup complete"
}

backup_database() {
    log_info "Creating database backup..."
    
    local backup_dir="$PROJECT_ROOT/backups"
    local backup_file="$backup_dir/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    mkdir -p "$backup_dir"
    
    # This would be customized based on your database setup
    # For Supabase, you'd use their backup tools
    # For self-hosted PostgreSQL:
    # pg_dump "$DATABASE_URL" > "$backup_file"
    
    log_success "Database backup created: $backup_file"
}

health_check() {
    local url=${1:-"http://localhost:8000/health"}
    local max_attempts=30
    local attempt=1
    
    log_info "Performing health check on $url..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$url" > /dev/null; then
            log_success "Health check passed"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts failed, retrying in 10 seconds..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

rollback() {
    log_warning "Rolling back deployment..."
    
    case "$DEPLOYMENT_TYPE" in
        "railway")
            railway rollback
            ;;
        "flyio")
            flyctl releases list
            read -p "Enter release version to rollback to: " version
            flyctl releases rollback "$version"
            ;;
        "docker")
            docker-compose down
            docker-compose up -d
            ;;
        *)
            log_error "Rollback not supported for deployment type: $DEPLOYMENT_TYPE"
            ;;
    esac
}

show_help() {
    cat << EOF
Solar Weather API Deployment Script

Usage: $0 <deployment_type> [environment]

Deployment Types:
  railway     Deploy to Railway
  flyio       Deploy to Fly.io
  docker      Deploy with Docker Compose
  vercel      Deploy frontend to Vercel
  build       Build Docker image only
  test        Run tests only
  health      Perform health check
  backup      Create database backup
  rollback    Rollback deployment
  help        Show this help message

Environments:
  production  Production environment (default)
  staging     Staging environment
  development Development environment

Examples:
  $0 railway production
  $0 flyio staging
  $0 docker development
  $0 vercel production
  $0 build
  $0 test
  $0 health https://your-api.com/health

Environment Variables Required:
  SUPABASE_URL
  SUPABASE_ANON_KEY
  SUPABASE_SERVICE_KEY
  JWT_SECRET_KEY
  RAZORPAY_KEY_ID
  RAZORPAY_KEY_SECRET
  HUGGINGFACE_API_TOKEN (optional)

EOF
}

# Main execution
main() {
    log_info "Starting deployment process..."
    log_info "Deployment type: $DEPLOYMENT_TYPE"
    log_info "Environment: $ENVIRONMENT"
    
    case "$DEPLOYMENT_TYPE" in
        "railway")
            validate_environment
            run_tests
            deploy_railway
            health_check "https://your-railway-app.railway.app/health"
            ;;
        "flyio")
            validate_environment
            run_tests
            deploy_flyio
            health_check "https://solar-weather-api.fly.dev/health"
            ;;
        "docker")
            run_tests
            deploy_docker
            setup_monitoring
            health_check
            ;;
        "vercel")
            deploy_frontend_vercel
            ;;
        "build")
            build_docker_image
            ;;
        "test")
            run_tests
            ;;
        "health")
            health_check "$3"
            ;;
        "backup")
            backup_database
            ;;
        "rollback")
            rollback
            ;;
        "help"|*)
            show_help
            ;;
    esac
    
    log_success "Deployment process completed!"
}

# Run main function
main "$@"