-- Migration 005: Functions and Triggers
-- Adds database functions and triggers for automation

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