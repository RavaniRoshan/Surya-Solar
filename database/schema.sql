-- Solar Weather API Database Schema
-- This file contains the complete database schema for the ZERO-COMP platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Predictions table for storing solar flare predictions
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    flare_probability DECIMAL(5,4) NOT NULL CHECK (flare_probability >= 0 AND flare_probability <= 1),
    severity_level TEXT NOT NULL CHECK (severity_level IN ('low', 'medium', 'high')),
    model_version TEXT NOT NULL DEFAULT 'surya-1.0',
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    raw_output JSONB,
    solar_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User subscriptions table for managing subscription tiers and API access
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tier TEXT NOT NULL CHECK (tier IN ('free', 'pro', 'enterprise')) DEFAULT 'free',
    razorpay_subscription_id TEXT UNIQUE,
    razorpay_customer_id TEXT,
    api_key_hash TEXT UNIQUE,
    webhook_url TEXT,
    alert_thresholds JSONB DEFAULT '{"low": 0.3, "medium": 0.6, "high": 0.8}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    subscription_start_date TIMESTAMPTZ DEFAULT NOW(),
    subscription_end_date TIMESTAMPTZ,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- API usage tracking for analytics and rate limiting
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    subscription_id UUID REFERENCES user_subscriptions(id) ON DELETE SET NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL DEFAULT 'GET',
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    ip_address INET,
    user_agent TEXT,
    api_key_used BOOLEAN DEFAULT FALSE,
    rate_limit_hit BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Alert notifications table for tracking sent alerts
CREATE TABLE IF NOT EXISTS alert_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id UUID NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    notification_type TEXT NOT NULL CHECK (notification_type IN ('websocket', 'webhook', 'email')),
    delivery_status TEXT NOT NULL CHECK (delivery_status IN ('pending', 'sent', 'failed', 'delivered')) DEFAULT 'pending',
    webhook_url TEXT,
    webhook_response_status INTEGER,
    webhook_response_body TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- System health metrics for monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name TEXT NOT NULL,
    metric_value DECIMAL,
    metric_unit TEXT,
    tags JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance optimization

-- Predictions indexes
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_severity ON predictions(severity_level);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_flare_probability ON predictions(flare_probability DESC);

-- User subscriptions indexes
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_tier ON user_subscriptions(tier);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_api_key_hash ON user_subscriptions(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_active ON user_subscriptions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_razorpay_subscription ON user_subscriptions(razorpay_subscription_id);

-- API usage indexes
CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_status_code ON api_usage(status_code);

-- Alert notifications indexes
CREATE INDEX IF NOT EXISTS idx_alert_notifications_user_id ON alert_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_prediction_id ON alert_notifications(prediction_id);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_status ON alert_notifications(delivery_status);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_type ON alert_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_scheduled_at ON alert_notifications(scheduled_at);

-- System metrics indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp DESC);

-- Row Level Security (RLS) policies

-- Enable RLS on user_subscriptions
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own subscription
CREATE POLICY user_subscriptions_select_policy ON user_subscriptions
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can only update their own subscription
CREATE POLICY user_subscriptions_update_policy ON user_subscriptions
    FOR UPDATE USING (auth.uid() = user_id);

-- Enable RLS on api_usage
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own API usage
CREATE POLICY api_usage_select_policy ON api_usage
    FOR SELECT USING (auth.uid() = user_id);

-- Enable RLS on alert_notifications
ALTER TABLE alert_notifications ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own alert notifications
CREATE POLICY alert_notifications_select_policy ON alert_notifications
    FOR SELECT USING (auth.uid() = user_id);

-- Functions and triggers for automatic timestamp updates

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER update_user_subscriptions_updated_at 
    BEFORE UPDATE ON user_subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically create user subscription on user creation
CREATE OR REPLACE FUNCTION create_user_subscription()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_subscriptions (user_id, tier, alert_thresholds)
    VALUES (
        NEW.id, 
        'free', 
        '{"low": 0.3, "medium": 0.6, "high": 0.8}'::jsonb
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to create subscription when user is created
CREATE TRIGGER create_user_subscription_trigger
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_user_subscription();

-- Views for common queries

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

-- Comments for documentation
COMMENT ON TABLE predictions IS 'Stores solar flare predictions from the Surya-1.0 model';
COMMENT ON TABLE user_subscriptions IS 'Manages user subscription tiers and API access configuration';
COMMENT ON TABLE api_usage IS 'Tracks API usage for analytics, billing, and rate limiting';
COMMENT ON TABLE alert_notifications IS 'Tracks alert notifications sent to users via various channels';
COMMENT ON TABLE system_metrics IS 'Stores system health and performance metrics';

COMMENT ON COLUMN predictions.flare_probability IS 'Solar flare probability between 0.0 and 1.0';
COMMENT ON COLUMN predictions.severity_level IS 'Severity classification: low, medium, or high';
COMMENT ON COLUMN predictions.confidence_score IS 'Model confidence score between 0.0 and 1.0';
COMMENT ON COLUMN predictions.raw_output IS 'Raw model output in JSON format';
COMMENT ON COLUMN predictions.solar_data IS 'Input solar data used for prediction in JSON format';

COMMENT ON COLUMN user_subscriptions.tier IS 'Subscription tier: free, pro, or enterprise';
COMMENT ON COLUMN user_subscriptions.api_key_hash IS 'SHA256 hash of the user API key';
COMMENT ON COLUMN user_subscriptions.alert_thresholds IS 'Custom alert thresholds for different severity levels';
COMMENT ON COLUMN user_subscriptions.webhook_url IS 'URL for webhook notifications';