-- Migration 004: Row Level Security Policies
-- Adds RLS policies for data security

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