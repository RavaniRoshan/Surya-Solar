-- User Alert Configurations Table
-- Stores user-defined alert triggers and delivery settings

CREATE TABLE IF NOT EXISTS user_alert_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Alert identification
    name VARCHAR(100) NOT NULL,
    
    -- Trigger settings
    trigger_source VARCHAR(50) NOT NULL CHECK (trigger_source IN ('flare_intensity', 'kp_index', 'solar_wind')),
    condition VARCHAR(20) NOT NULL DEFAULT 'greater_than' CHECK (condition IN ('greater_than', 'less_than', 'equals')),
    threshold DECIMAL(10, 4) NOT NULL,
    
    -- Delivery channels (stored as JSONB)
    delivery_channels JSONB NOT NULL DEFAULT '{"email": true, "webhook": false, "discord": false, "slack": false}',
    
    -- Webhook configuration
    webhook_url TEXT,
    webhook_payload JSONB,
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    triggered_count INTEGER NOT NULL DEFAULT 0,
    last_triggered_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_user_alert_configs_user_id ON user_alert_configs(user_id);
CREATE INDEX idx_user_alert_configs_active ON user_alert_configs(is_active) WHERE is_active = true;
CREATE INDEX idx_user_alert_configs_trigger ON user_alert_configs(trigger_source);

-- Row Level Security
ALTER TABLE user_alert_configs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own alert configs
CREATE POLICY "Users can view own alert configs" ON user_alert_configs
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can insert their own alert configs
CREATE POLICY "Users can create alert configs" ON user_alert_configs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own alert configs
CREATE POLICY "Users can update own alert configs" ON user_alert_configs
    FOR UPDATE USING (auth.uid() = user_id);

-- Policy: Users can delete their own alert configs
CREATE POLICY "Users can delete own alert configs" ON user_alert_configs
    FOR DELETE USING (auth.uid() = user_id);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_user_alert_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_alert_configs_updated_at
    BEFORE UPDATE ON user_alert_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_user_alert_configs_updated_at();

-- Comments
COMMENT ON TABLE user_alert_configs IS 'User-defined alert configurations for solar event notifications';
COMMENT ON COLUMN user_alert_configs.trigger_source IS 'Type of solar event to monitor: flare_intensity, kp_index, solar_wind';
COMMENT ON COLUMN user_alert_configs.condition IS 'Comparison condition: greater_than, less_than, equals';
COMMENT ON COLUMN user_alert_configs.threshold IS 'Threshold value for triggering the alert';
COMMENT ON COLUMN user_alert_configs.delivery_channels IS 'JSON object with channel toggles: email, webhook, discord, slack';
