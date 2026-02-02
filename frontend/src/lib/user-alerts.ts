/**
 * User Alerts API Client
 * Frontend hooks for managing user alert configurations
 */

import { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface DeliveryChannels {
    email: boolean;
    webhook: boolean;
    discord: boolean;
    slack: boolean;
}

export interface AlertConfig {
    id: string;
    user_id: string;
    name: string;
    trigger_source: 'flare_intensity' | 'kp_index' | 'solar_wind';
    condition: 'greater_than' | 'less_than' | 'equals';
    threshold: number;
    delivery_channels: DeliveryChannels;
    webhook_url?: string;
    webhook_payload?: Record<string, unknown>;
    is_active: boolean;
    triggered_count: number;
    last_triggered_at?: string;
    created_at: string;
    updated_at: string;
}

export interface CreateAlertConfig {
    name: string;
    trigger_source: 'flare_intensity' | 'kp_index' | 'solar_wind';
    condition?: 'greater_than' | 'less_than' | 'equals';
    threshold: number;
    delivery_channels?: Partial<DeliveryChannels>;
    webhook_url?: string;
    webhook_payload?: Record<string, unknown>;
    is_active?: boolean;
}

export interface UpdateAlertConfig {
    name?: string;
    trigger_source?: 'flare_intensity' | 'kp_index' | 'solar_wind';
    condition?: 'greater_than' | 'less_than' | 'equals';
    threshold?: number;
    delivery_channels?: Partial<DeliveryChannels>;
    webhook_url?: string;
    webhook_payload?: Record<string, unknown>;
    is_active?: boolean;
}

// API Functions
async function getAuthHeaders(): Promise<HeadersInit> {
    // Get token from localStorage or session
    const token = typeof window !== 'undefined'
        ? localStorage.getItem('access_token')
        : null;

    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
}

export async function fetchUserAlerts(): Promise<AlertConfig[]> {
    const headers = await getAuthHeaders();

    const response = await fetch(`${API_BASE}/api/v1/user/alerts`, {
        method: 'GET',
        headers
    });

    if (!response.ok) {
        throw new Error(`Failed to fetch alerts: ${response.statusText}`);
    }

    const data = await response.json();
    return data.alerts;
}

export async function createAlert(config: CreateAlertConfig): Promise<AlertConfig> {
    const headers = await getAuthHeaders();

    const response = await fetch(`${API_BASE}/api/v1/user/alerts`, {
        method: 'POST',
        headers,
        body: JSON.stringify(config)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create alert');
    }

    return response.json();
}

export async function updateAlert(alertId: string, config: UpdateAlertConfig): Promise<AlertConfig> {
    const headers = await getAuthHeaders();

    const response = await fetch(`${API_BASE}/api/v1/user/alerts/${alertId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(config)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update alert');
    }

    return response.json();
}

export async function deleteAlert(alertId: string): Promise<void> {
    const headers = await getAuthHeaders();

    const response = await fetch(`${API_BASE}/api/v1/user/alerts/${alertId}`, {
        method: 'DELETE',
        headers
    });

    if (!response.ok) {
        throw new Error('Failed to delete alert');
    }
}

export async function toggleAlert(alertId: string): Promise<AlertConfig> {
    const headers = await getAuthHeaders();

    const response = await fetch(`${API_BASE}/api/v1/user/alerts/${alertId}/toggle`, {
        method: 'POST',
        headers
    });

    if (!response.ok) {
        throw new Error('Failed to toggle alert');
    }

    return response.json();
}

// React Hook
export function useUserAlerts() {
    const [alerts, setAlerts] = useState<AlertConfig[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchAlerts = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await fetchUserAlerts();
            setAlerts(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load alerts');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAlerts();
    }, [fetchAlerts]);

    const create = useCallback(async (config: CreateAlertConfig) => {
        const newAlert = await createAlert(config);
        setAlerts(prev => [newAlert, ...prev]);
        return newAlert;
    }, []);

    const update = useCallback(async (alertId: string, config: UpdateAlertConfig) => {
        const updated = await updateAlert(alertId, config);
        setAlerts(prev => prev.map(a => a.id === alertId ? updated : a));
        return updated;
    }, []);

    const remove = useCallback(async (alertId: string) => {
        await deleteAlert(alertId);
        setAlerts(prev => prev.filter(a => a.id !== alertId));
    }, []);

    const toggle = useCallback(async (alertId: string) => {
        const updated = await toggleAlert(alertId);
        setAlerts(prev => prev.map(a => a.id === alertId ? updated : a));
        return updated;
    }, []);

    return {
        alerts,
        loading,
        error,
        refetch: fetchAlerts,
        createAlert: create,
        updateAlert: update,
        deleteAlert: remove,
        toggleAlert: toggle
    };
}
