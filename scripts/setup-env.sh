#!/bin/bash

# Environment Setup Script for Solar Weather API
# Creates environment-specific configuration files

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
ENVIRONMENT=${1:-"development"}

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

generate_secret() {
    openssl rand -hex 32
}

create_env_file() {
    local env_file="$PROJECT_ROOT/.env.$ENVIRONMENT"
    
    log_info "Creating environment file: $env_file"
    
    cat > "$env_file" << EOF
# Solar Weather API Environment Configuration
# Environment: $ENVIRONMENT
# Generated: $(date)

# Application Settings
ENVIRONMENT=$ENVIRONMENT
APP_NAME=ZERO-COMP Solar Weather API
APP_VERSION=1.0.0
DEBUG=$([ "$ENVIRONMENT" = "development" ] && echo "true" || echo "false")

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Database Configuration
# Replace with your actual Supabase credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/solar_weather_$ENVIRONMENT

# Authentication
JWT_SECRET_KEY=$(generate_secret)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# External Services
HUGGINGFACE_API_TOKEN=your-huggingface-token-here
NASA_API_KEY=your-nasa-api-key-here
NASA_BASE_URL=https://api.nasa.gov

# Payment Processing
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret
RAZORPAY_WEBHOOK_SECRET=your-razorpay-webhook-secret

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=$([ "$ENVIRONMENT" = "development" ] && echo "DEBUG" || echo "INFO")
LOG_FORMAT=json
LOG_FILE=./logs/app.log

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,https://your-frontend-domain.com

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Model Configuration
MODEL_NAME=nasa-ibm/surya-1.0
MODEL_CACHE_DIR=./model_cache
INFERENCE_TIMEOUT_SECONDS=30
PREDICTION_INTERVAL_MINUTES=10

# Monitoring and Health Checks
HEALTH_CHECK_INTERVAL=30
METRICS_ENABLED=true
SENTRY_DSN=your-sentry-dsn-here

EOF

    log_success "Environment file created: $env_file"
}

create_frontend_env() {
    local frontend_env="$PROJECT_ROOT/frontend/.env.$ENVIRONMENT"
    
    log_info "Creating frontend environment file: $frontend_env"
    
    # Determine API URLs based on environment
    local api_url
    local ws_url
    
    case "$ENVIRONMENT" in
        "development")
            api_url="http://localhost:8000"
            ws_url="ws://localhost:8000"
            ;;
        "staging")
            api_url="https://staging-api.your-domain.com"
            ws_url="wss://staging-api.your-domain.com"
            ;;
        "production")
            api_url="https://api.your-domain.com"
            ws_url="wss://api.your-domain.com"
            ;;
    esac
    
    cat > "$frontend_env" << EOF
# Frontend Environment Configuration
# Environment: $ENVIRONMENT
# Generated: $(date)

# Next.js Configuration
NODE_ENV=$ENVIRONMENT
NEXT_PUBLIC_APP_NAME=ZERO-COMP Solar Weather Dashboard
NEXT_PUBLIC_APP_VERSION=1.0.0

# API Configuration
NEXT_PUBLIC_API_URL=$api_url
NEXT_PUBLIC_WS_URL=$ws_url

# Supabase Configuration (Public keys only)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# Analytics and Monitoring
NEXT_PUBLIC_GA_TRACKING_ID=your-google-analytics-id
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn-here

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=$([ "$ENVIRONMENT" = "production" ] && echo "true" || echo "false")
NEXT_PUBLIC_ENABLE_DEBUG=$([ "$ENVIRONMENT" = "development" ] && echo "true" || echo "false")

# Payment Configuration
NEXT_PUBLIC_RAZORPAY_KEY_ID=your-razorpay-key-id

EOF

    log_success "Frontend environment file created: $frontend_env"
}

create_docker_env() {
    local docker_env="$PROJECT_ROOT/.env.docker"
    
    log_info "Creating Docker environment file: $docker_env"
    
    cat > "$docker_env" << EOF
# Docker Compose Environment Variables
# Generated: $(date)

# Database
POSTGRES_DB=solar_weather_$ENVIRONMENT
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(generate_secret | cut -c1-16)

# Redis
REDIS_PASSWORD=$(generate_secret | cut -c1-16)

# Application
ENVIRONMENT=$ENVIRONMENT
JWT_SECRET_KEY=$(generate_secret)

# External Services (replace with actual values)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret
HUGGINGFACE_API_TOKEN=your-huggingface-token-here

# Frontend URLs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

EOF

    log_success "Docker environment file created: $docker_env"
}

create_deployment_configs() {
    log_info "Creating deployment-specific configurations..."
    
    # Railway configuration
    if [[ "$ENVIRONMENT" = "production" ]]; then
        cat > "$PROJECT_ROOT/railway.prod.json" << EOF
{
  "\$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt",
    "watchPatterns": ["**/*.py", "requirements.txt", "app/**/*"]
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port \$PORT --workers 2",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
EOF
    fi
    
    # Fly.io production configuration
    if [[ "$ENVIRONMENT" = "production" ]]; then
        cat > "$PROJECT_ROOT/fly.prod.toml" << EOF
app = "solar-weather-api-prod"
primary_region = "ord"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  ENVIRONMENT = "production"
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 2

[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 1024

[processes]
  app = "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"
  scheduler = "python -m app.cli.scheduler"
EOF
    fi
    
    log_success "Deployment configurations created"
}

setup_ssl_certificates() {
    local ssl_dir="$PROJECT_ROOT/ssl"
    
    if [[ "$ENVIRONMENT" = "development" ]]; then
        log_info "Creating self-signed SSL certificates for development..."
        
        mkdir -p "$ssl_dir"
        
        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$ssl_dir/key.pem" \
            -out "$ssl_dir/cert.pem" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        log_success "Self-signed SSL certificates created in $ssl_dir"
        log_warning "These certificates are for development only!"
    else
        log_info "For production, obtain SSL certificates from Let's Encrypt or your certificate provider"
        log_info "Place certificates in $ssl_dir/cert.pem and $ssl_dir/key.pem"
    fi
}

create_database_migrations() {
    local migrations_dir="$PROJECT_ROOT/database/migrations"
    
    log_info "Creating database migration structure..."
    
    mkdir -p "$migrations_dir"
    
    cat > "$migrations_dir/001_initial_schema.sql" << EOF
-- Initial database schema for Solar Weather API
-- Generated: $(date)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    flare_probability DECIMAL(5,4) NOT NULL CHECK (flare_probability >= 0 AND flare_probability <= 1),
    severity_level TEXT NOT NULL CHECK (severity_level IN ('low', 'medium', 'high')),
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    model_version TEXT NOT NULL DEFAULT 'surya-1.0',
    raw_output JSONB,
    solar_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User subscriptions table
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('free', 'pro', 'enterprise')),
    razorpay_subscription_id TEXT,
    api_key_hash TEXT UNIQUE,
    webhook_url TEXT,
    alert_thresholds JSONB DEFAULT '{"low": 0.3, "medium": 0.6, "high": 0.8}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- API usage tracking table
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_severity ON predictions(severity_level);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_api_key ON user_subscriptions(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_api_usage_user_timestamp ON api_usage(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);

-- Functions for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS \$\$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
\$\$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_predictions_updated_at BEFORE UPDATE ON predictions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_subscriptions_updated_at BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EOF

    log_success "Database migration files created in $migrations_dir"
}

validate_configuration() {
    log_info "Validating configuration..."
    
    local env_file="$PROJECT_ROOT/.env.$ENVIRONMENT"
    
    if [[ ! -f "$env_file" ]]; then
        log_error "Environment file not found: $env_file"
        return 1
    fi
    
    # Check for required variables
    local required_vars=(
        "ENVIRONMENT"
        "SUPABASE_URL"
        "SUPABASE_ANON_KEY"
        "JWT_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$env_file"; then
            log_error "Required variable $var not found in $env_file"
            return 1
        fi
    done
    
    log_success "Configuration validation passed"
}

show_help() {
    cat << EOF
Environment Setup Script for Solar Weather API

Usage: $0 [environment]

Environments:
  development  Development environment (default)
  staging      Staging environment
  production   Production environment

This script creates:
  - Environment configuration files (.env.*)
  - Frontend environment files
  - Docker environment files
  - SSL certificates (development only)
  - Database migration files
  - Deployment configurations

After running this script:
  1. Edit the generated .env files with your actual credentials
  2. Review and customize the configuration as needed
  3. Run database migrations if needed
  4. Start the application

EOF
}

# Main execution
main() {
    log_info "Setting up environment: $ENVIRONMENT"
    
    case "$1" in
        "help"|"-h"|"--help")
            show_help
            exit 0
            ;;
    esac
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/model_cache"
    mkdir -p "$PROJECT_ROOT/backups"
    
    # Generate configuration files
    create_env_file
    create_frontend_env
    create_docker_env
    create_deployment_configs
    setup_ssl_certificates
    create_database_migrations
    
    # Validate configuration
    validate_configuration
    
    log_success "Environment setup completed for: $ENVIRONMENT"
    log_warning "Remember to:"
    log_warning "1. Update .env.$ENVIRONMENT with your actual credentials"
    log_warning "2. Update frontend/.env.$ENVIRONMENT with your settings"
    log_warning "3. Review and test the configuration"
    log_warning "4. Keep sensitive files secure and out of version control"
}

# Run main function
main "$@"