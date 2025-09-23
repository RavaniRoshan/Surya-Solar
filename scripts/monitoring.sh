#!/bin/bash

# Monitoring and Health Check Script for Solar Weather API
# Provides system monitoring, alerting, and automated recovery

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
MONITORING_TYPE=${1:-"help"}
API_URL=${API_URL:-"http://localhost:8000"}
ALERT_EMAIL=${ALERT_EMAIL:-"admin@your-domain.com"}
SLACK_WEBHOOK=${SLACK_WEBHOOK:-""}

# Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=80
DISK_THRESHOLD=85
RESPONSE_TIME_THRESHOLD=2000  # milliseconds
ERROR_RATE_THRESHOLD=5        # percentage

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

send_alert() {
    local message="$1"
    local severity="${2:-INFO}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    log_warning "ALERT [$severity]: $message"
    
    # Log to file
    echo "[$timestamp] [$severity] $message" >> "$PROJECT_ROOT/logs/alerts.log"
    
    # Send email alert (if configured)
    if command -v mail &> /dev/null && [[ -n "$ALERT_EMAIL" ]]; then
        echo "$message" | mail -s "Solar Weather API Alert [$severity]" "$ALERT_EMAIL"
    fi
    
    # Send Slack notification (if configured)
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 Solar Weather API Alert [$severity]\\n$message\"}" \
            "$SLACK_WEBHOOK" 2>/dev/null || true
    fi
}

check_api_health() {
    local url="$API_URL/health"
    local start_time=$(date +%s%3N)
    
    log_info "Checking API health: $url"
    
    # Make health check request
    local response=$(curl -s -w "%{http_code},%{time_total}" -o /tmp/health_response "$url" 2>/dev/null || echo "000,0")
    local http_code=$(echo "$response" | cut -d',' -f1)
    local response_time=$(echo "$response" | cut -d',' -f2)
    local response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d'.' -f1)
    
    # Check HTTP status
    if [[ "$http_code" != "200" ]]; then
        send_alert "API health check failed: HTTP $http_code" "CRITICAL"
        return 1
    fi
    
    # Check response time
    if [[ "$response_time_ms" -gt "$RESPONSE_TIME_THRESHOLD" ]]; then
        send_alert "API response time high: ${response_time_ms}ms (threshold: ${RESPONSE_TIME_THRESHOLD}ms)" "WARNING"
    fi
    
    # Parse health response
    if [[ -f "/tmp/health_response" ]]; then
        local status=$(jq -r '.status' /tmp/health_response 2>/dev/null || echo "unknown")
        local database_status=$(jq -r '.database.status' /tmp/health_response 2>/dev/null || echo "unknown")
        local model_status=$(jq -r '.model.status' /tmp/health_response 2>/dev/null || echo "unknown")
        
        if [[ "$status" != "healthy" ]]; then
            send_alert "API status unhealthy: $status" "CRITICAL"
            return 1
        fi
        
        if [[ "$database_status" != "connected" ]]; then
            send_alert "Database connection failed: $database_status" "CRITICAL"
        fi
        
        if [[ "$model_status" != "loaded" ]]; then
            send_alert "ML model not loaded: $model_status" "WARNING"
        fi
    fi
    
    log_success "API health check passed (${response_time_ms}ms)"
    return 0
}

check_system_resources() {
    log_info "Checking system resources..."
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d',' -f1)
    cpu_usage=${cpu_usage%.*}  # Remove decimal part
    
    if [[ "$cpu_usage" -gt "$CPU_THRESHOLD" ]]; then
        send_alert "High CPU usage: ${cpu_usage}% (threshold: ${CPU_THRESHOLD}%)" "WARNING"
    fi
    
    # Memory usage
    local memory_info=$(free | grep Mem)
    local total_memory=$(echo "$memory_info" | awk '{print $2}')
    local used_memory=$(echo "$memory_info" | awk '{print $3}')
    local memory_usage=$((used_memory * 100 / total_memory))
    
    if [[ "$memory_usage" -gt "$MEMORY_THRESHOLD" ]]; then
        send_alert "High memory usage: ${memory_usage}% (threshold: ${MEMORY_THRESHOLD}%)" "WARNING"
    fi
    
    # Disk usage
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    if [[ "$disk_usage" -gt "$DISK_THRESHOLD" ]]; then
        send_alert "High disk usage: ${disk_usage}% (threshold: ${DISK_THRESHOLD}%)" "WARNING"
    fi
    
    log_success "System resources check completed"
    log_info "CPU: ${cpu_usage}%, Memory: ${memory_usage}%, Disk: ${disk_usage}%"
}

check_docker_containers() {
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not available, skipping container checks"
        return 0
    fi
    
    log_info "Checking Docker containers..."
    
    local containers=("solar-weather-api" "solar-weather-scheduler" "postgres" "redis")
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            local status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not_found")
            
            if [[ "$status" != "running" ]]; then
                send_alert "Container $container is not running: $status" "CRITICAL"
                
                # Attempt to restart container
                log_info "Attempting to restart container: $container"
                docker restart "$container" 2>/dev/null || send_alert "Failed to restart container: $container" "CRITICAL"
            else
                log_success "Container $container is running"
            fi
        else
            log_warning "Container $container not found"
        fi
    done
}

check_database_connections() {
    log_info "Checking database connections..."
    
    # Check if we can connect to the database
    local db_check_url="$API_URL/health/database"
    local response=$(curl -s "$db_check_url" 2>/dev/null || echo '{"status":"error"}')
    local db_status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "error")
    
    if [[ "$db_status" != "connected" ]]; then
        send_alert "Database connection check failed: $db_status" "CRITICAL"
        return 1
    fi
    
    # Check connection pool if available
    local pool_info=$(echo "$response" | jq -r '.pool_info' 2>/dev/null)
    if [[ "$pool_info" != "null" && "$pool_info" != "" ]]; then
        local active_connections=$(echo "$pool_info" | jq -r '.active' 2>/dev/null || echo "0")
        local max_connections=$(echo "$pool_info" | jq -r '.max' 2>/dev/null || echo "100")
        local connection_usage=$((active_connections * 100 / max_connections))
        
        if [[ "$connection_usage" -gt 80 ]]; then
            send_alert "High database connection usage: ${connection_usage}% (${active_connections}/${max_connections})" "WARNING"
        fi
    fi
    
    log_success "Database connections check passed"
}

check_prediction_pipeline() {
    log_info "Checking prediction pipeline..."
    
    # Check last prediction timestamp
    local predictions_url="$API_URL/api/v1/alerts/current"
    local response=$(curl -s -H "Authorization: Bearer test-token" "$predictions_url" 2>/dev/null || echo '{}')
    local last_updated=$(echo "$response" | jq -r '.last_updated' 2>/dev/null || echo "null")
    
    if [[ "$last_updated" != "null" ]]; then
        local last_timestamp=$(date -d "$last_updated" +%s 2>/dev/null || echo "0")
        local current_timestamp=$(date +%s)
        local time_diff=$((current_timestamp - last_timestamp))
        
        # Alert if no predictions in the last 30 minutes
        if [[ "$time_diff" -gt 1800 ]]; then
            send_alert "No recent predictions: last update was $(($time_diff / 60)) minutes ago" "WARNING"
        fi
    else
        send_alert "Unable to retrieve prediction status" "WARNING"
    fi
    
    log_success "Prediction pipeline check completed"
}

check_websocket_connections() {
    log_info "Checking WebSocket connections..."
    
    # Test WebSocket connection
    local ws_url="${API_URL/http/ws}/ws/alerts?token=test-token"
    
    # Use websocat if available, otherwise skip
    if command -v websocat &> /dev/null; then
        local ws_test=$(timeout 10s websocat "$ws_url" <<< '{"type":"ping"}' 2>/dev/null || echo "failed")
        
        if [[ "$ws_test" == *"pong"* ]]; then
            log_success "WebSocket connection test passed"
        else
            send_alert "WebSocket connection test failed" "WARNING"
        fi
    else
        log_warning "websocat not available, skipping WebSocket test"
    fi
}

generate_monitoring_report() {
    local report_file="$PROJECT_ROOT/logs/monitoring_report_$(date +%Y%m%d_%H%M%S).json"
    
    log_info "Generating monitoring report: $report_file"
    
    # Collect system metrics
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d',' -f1)
    local memory_info=$(free | grep Mem)
    local total_memory=$(echo "$memory_info" | awk '{print $2}')
    local used_memory=$(echo "$memory_info" | awk '{print $3}')
    local memory_usage=$((used_memory * 100 / total_memory))
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    # API health check
    local api_response=$(curl -s -w "%{http_code},%{time_total}" -o /tmp/api_health "$API_URL/health" 2>/dev/null || echo "000,0")
    local api_status=$(echo "$api_response" | cut -d',' -f1)
    local api_response_time=$(echo "$api_response" | cut -d',' -f2)
    
    # Generate JSON report
    cat > "$report_file" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "system": {
    "cpu_usage_percent": $cpu_usage,
    "memory_usage_percent": $memory_usage,
    "disk_usage_percent": $disk_usage,
    "uptime": "$(uptime -p)"
  },
  "api": {
    "status_code": $api_status,
    "response_time_seconds": $api_response_time,
    "health_status": "$(cat /tmp/api_health 2>/dev/null | jq -r '.status' 2>/dev/null || echo 'unknown')"
  },
  "thresholds": {
    "cpu_threshold": $CPU_THRESHOLD,
    "memory_threshold": $MEMORY_THRESHOLD,
    "disk_threshold": $DISK_THRESHOLD,
    "response_time_threshold_ms": $RESPONSE_TIME_THRESHOLD
  }
}
EOF
    
    log_success "Monitoring report generated: $report_file"
}

cleanup_old_logs() {
    log_info "Cleaning up old log files..."
    
    local logs_dir="$PROJECT_ROOT/logs"
    
    # Remove logs older than 30 days
    find "$logs_dir" -name "*.log" -type f -mtime +30 -delete 2>/dev/null || true
    find "$logs_dir" -name "monitoring_report_*.json" -type f -mtime +7 -delete 2>/dev/null || true
    
    # Compress logs older than 7 days
    find "$logs_dir" -name "*.log" -type f -mtime +7 ! -name "*.gz" -exec gzip {} \; 2>/dev/null || true
    
    log_success "Log cleanup completed"
}

run_full_monitoring() {
    log_info "Running full monitoring suite..."
    
    local start_time=$(date +%s)
    local failed_checks=0
    
    # Run all checks
    check_api_health || ((failed_checks++))
    check_system_resources || ((failed_checks++))
    check_docker_containers || ((failed_checks++))
    check_database_connections || ((failed_checks++))
    check_prediction_pipeline || ((failed_checks++))
    check_websocket_connections || ((failed_checks++))
    
    # Generate report
    generate_monitoring_report
    
    # Cleanup
    cleanup_old_logs
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [[ $failed_checks -eq 0 ]]; then
        log_success "All monitoring checks passed (${duration}s)"
    else
        log_error "$failed_checks monitoring checks failed (${duration}s)"
        send_alert "$failed_checks monitoring checks failed" "WARNING"
    fi
    
    return $failed_checks
}

setup_monitoring_cron() {
    log_info "Setting up monitoring cron jobs..."
    
    local cron_file="/tmp/solar_weather_monitoring_cron"
    
    cat > "$cron_file" << EOF
# Solar Weather API Monitoring Cron Jobs
# Full monitoring every 5 minutes
*/5 * * * * $SCRIPT_DIR/monitoring.sh full >> $PROJECT_ROOT/logs/monitoring.log 2>&1

# Health check every minute
* * * * * $SCRIPT_DIR/monitoring.sh health >> $PROJECT_ROOT/logs/health.log 2>&1

# System resources every 10 minutes
*/10 * * * * $SCRIPT_DIR/monitoring.sh resources >> $PROJECT_ROOT/logs/resources.log 2>&1

# Daily cleanup at 2 AM
0 2 * * * $SCRIPT_DIR/monitoring.sh cleanup >> $PROJECT_ROOT/logs/cleanup.log 2>&1
EOF
    
    # Install cron jobs
    crontab "$cron_file"
    rm "$cron_file"
    
    log_success "Monitoring cron jobs installed"
}

show_help() {
    cat << EOF
Solar Weather API Monitoring Script

Usage: $0 <command> [options]

Commands:
  health      Check API health endpoint
  resources   Check system resources (CPU, memory, disk)
  containers  Check Docker containers status
  database    Check database connections
  pipeline    Check prediction pipeline
  websocket   Check WebSocket connections
  full        Run all monitoring checks
  report      Generate monitoring report only
  cleanup     Clean up old log files
  setup-cron  Set up monitoring cron jobs
  help        Show this help message

Environment Variables:
  API_URL           API base URL (default: http://localhost:8000)
  ALERT_EMAIL       Email for alerts
  SLACK_WEBHOOK     Slack webhook URL for notifications

Thresholds:
  CPU_THRESHOLD     CPU usage threshold (default: 80%)
  MEMORY_THRESHOLD  Memory usage threshold (default: 80%)
  DISK_THRESHOLD    Disk usage threshold (default: 85%)
  RESPONSE_TIME_THRESHOLD  Response time threshold (default: 2000ms)

Examples:
  $0 health
  $0 full
  API_URL=https://api.example.com $0 health
  $0 setup-cron

EOF
}

# Main execution
main() {
    # Create logs directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/logs"
    
    case "$MONITORING_TYPE" in
        "health")
            check_api_health
            ;;
        "resources")
            check_system_resources
            ;;
        "containers")
            check_docker_containers
            ;;
        "database")
            check_database_connections
            ;;
        "pipeline")
            check_prediction_pipeline
            ;;
        "websocket")
            check_websocket_connections
            ;;
        "full")
            run_full_monitoring
            ;;
        "report")
            generate_monitoring_report
            ;;
        "cleanup")
            cleanup_old_logs
            ;;
        "setup-cron")
            setup_monitoring_cron
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"