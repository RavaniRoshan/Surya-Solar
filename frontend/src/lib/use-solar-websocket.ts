/**
 * useSolarWebSocket Hook
 * Real-time solar weather data via WebSocket
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import WebSocketClient, { getWebSocketClient, AlertWebSocketMessage, ConnectionStatus } from './websocket-client';

export interface SolarEvent {
    id: string;
    type: 'flare' | 'cme' | 'activity' | 'sync';
    title: string;
    description: string;
    severity: 'low' | 'medium' | 'high';
    timestamp: string;
}

export interface SolarPrediction {
    probability: number;
    severity: 'low' | 'medium' | 'high';
    solarWindSpeed: number;
    kpIndex: number;
    magneticField: number;
    lastUpdated: string;
}

export interface UseSolarWebSocketReturn {
    // Connection state
    isConnected: boolean;
    reconnecting: boolean;
    error: string | null;

    // Data
    prediction: SolarPrediction | null;
    events: SolarEvent[];

    // Actions
    connect: () => Promise<void>;
    disconnect: () => void;
}

export function useSolarWebSocket(): UseSolarWebSocketReturn {
    const clientRef = useRef<WebSocketClient | null>(null);
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
        connected: false,
        reconnecting: false,
        reconnectAttempts: 0
    });

    const [prediction, setPrediction] = useState<SolarPrediction | null>(null);
    const [events, setEvents] = useState<SolarEvent[]>([]);

    // Handle incoming messages
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleMessage = useCallback((message: AlertWebSocketMessage | Record<string, any>) => {
        if (message.type === 'alert' && 'data' in message && message.data) {
            const data = message.data as AlertWebSocketMessage['data'];
            // Update prediction data
            setPrediction({
                probability: data.current_probability || 0,
                severity: data.severity_level || 'low',
                solarWindSpeed: (data as Record<string, number>).solar_wind_speed || 450,
                kpIndex: (data as Record<string, number>).kp_index || 2,
                magneticField: (data as Record<string, number>).magnetic_field || 5.4,
                lastUpdated: data.last_updated || new Date().toISOString()
            });

            // Add event if it's high severity
            if (data.alert_active || data.severity_level === 'high') {
                const newEvent: SolarEvent = {
                    id: `event-${Date.now()}`,
                    type: 'flare',
                    title: `${data.severity_level?.toUpperCase()}-Class Activity`,
                    description: `Probability: ${(data.current_probability * 100).toFixed(0)}%`,
                    severity: data.severity_level || 'medium',
                    timestamp: new Date().toISOString()
                };

                setEvents(prev => [newEvent, ...prev].slice(0, 50)); // Keep last 50 events
            }
        }

        if (message.type === 'heartbeat') {
            // Could update last ping time if needed
        }
    }, []);

    // Connect to WebSocket
    const connect = useCallback(async () => {
        if (!clientRef.current) {
            clientRef.current = getWebSocketClient();
        }

        // Subscribe to connection status
        clientRef.current.onConnectionStatus((status) => {
            setConnectionStatus(status);
        });

        // Subscribe to messages
        clientRef.current.onMessage(handleMessage);

        // Connect
        await clientRef.current.connect();
    }, [handleMessage]);

    // Disconnect from WebSocket
    const disconnect = useCallback(() => {
        if (clientRef.current) {
            clientRef.current.disconnect();
        }
    }, []);

    // Auto-connect on mount
    useEffect(() => {
        connect();

        return () => {
            disconnect();
        };
    }, [connect, disconnect]);

    // Generate mock events for demo purposes (remove in production)
    useEffect(() => {
        const mockEvents: SolarEvent[] = [
            {
                id: '1',
                type: 'flare',
                title: 'X-Class Flare Detected',
                description: 'Magnitude 1.2 from Active Region 3664. Probability of HF Radio Blackout: 85%.',
                severity: 'high',
                timestamp: new Date(Date.now() - 5 * 60000).toISOString()
            },
            {
                id: '2',
                type: 'activity',
                title: 'M-Class Activity Increase',
                description: 'Surya-1.0 forecasting 3 consecutive M-class events in next 12 hours.',
                severity: 'medium',
                timestamp: new Date(Date.now() - 15 * 60000).toISOString()
            },
            {
                id: '3',
                type: 'sync',
                title: 'Satellite Data Sync Complete',
                description: 'GOES-16 Full Spectral Data synchronized with 99.9% integrity.',
                severity: 'low',
                timestamp: new Date(Date.now() - 30 * 60000).toISOString()
            }
        ];

        if (events.length === 0) {
            setEvents(mockEvents);
        }

        // Set initial mock prediction if not connected
        if (!prediction) {
            setPrediction({
                probability: 0.942,
                severity: 'medium',
                solarWindSpeed: 450,
                kpIndex: 2,
                magneticField: 5.4,
                lastUpdated: new Date().toISOString()
            });
        }
    }, [events.length, prediction]);

    return {
        isConnected: connectionStatus.connected,
        reconnecting: connectionStatus.reconnecting,
        error: connectionStatus.error || null,
        prediction,
        events,
        connect,
        disconnect
    };
}

export default useSolarWebSocket;
