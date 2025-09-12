-- Migration 003: System Metrics
-- Adds system metrics table for monitoring

-- System health metrics table
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name TEXT NOT NULL,
    metric_value DECIMAL,
    metric_unit TEXT,
    tags JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for system metrics
CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp DESC);