-- Migration 002: Alert Notifications
-- Adds alert notifications table and related functionality

-- Alert notifications table
CREATE TABLE alert_notifications (
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

-- Indexes for alert notifications
CREATE INDEX idx_alert_notifications_user_id ON alert_notifications(user_id);
CREATE INDEX idx_alert_notifications_prediction_id ON alert_notifications(prediction_id);
CREATE INDEX idx_alert_notifications_status ON alert_notifications(delivery_status);
CREATE INDEX idx_alert_notifications_type ON alert_notifications(notification_type);
CREATE INDEX idx_alert_notifications_scheduled_at ON alert_notifications(scheduled_at);