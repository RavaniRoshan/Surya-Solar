-- Migration 006: Database Views
-- Adds useful views for common queries

-- View for current active predictions (last 24 hours)
CREATE OR REPLACE VIEW current_predictions AS
SELECT 
    id,
    timestamp,
    flare_probability,
    severity_level,
    model_version,
    confidence_score,
    created_at
FROM predictions
WHERE timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- View for user subscription details with usage stats
CREATE OR REPLACE VIEW user_subscription_details AS
SELECT 
    us.id,
    us.user_id,
    us.tier,
    us.is_active,
    us.subscription_start_date,
    us.subscription_end_date,
    us.alert_thresholds,
    us.webhook_url,
    us.last_login,
    COUNT(au.id) as total_api_calls,
    MAX(au.timestamp) as last_api_call
FROM user_subscriptions us
LEFT JOIN api_usage au ON us.user_id = au.user_id
GROUP BY us.id, us.user_id, us.tier, us.is_active, us.subscription_start_date, 
         us.subscription_end_date, us.alert_thresholds, us.webhook_url, us.last_login;

-- View for prediction statistics
CREATE OR REPLACE VIEW prediction_statistics AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as prediction_count,
    AVG(flare_probability) as avg_probability,
    MAX(flare_probability) as max_probability,
    COUNT(CASE WHEN severity_level = 'high' THEN 1 END) as high_severity_count,
    COUNT(CASE WHEN severity_level = 'medium' THEN 1 END) as medium_severity_count,
    COUNT(CASE WHEN severity_level = 'low' THEN 1 END) as low_severity_count
FROM predictions
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;