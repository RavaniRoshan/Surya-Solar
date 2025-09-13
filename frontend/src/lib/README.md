# WebSocket Integration

This directory contains the WebSocket integration for real-time solar weather alerts.

## Components

### WebSocket Client (`websocket-client.ts`)
- Manages WebSocket connections to the backend
- Handles authentication via Supabase tokens
- Implements automatic reconnection with exponential backoff
- Provides heartbeat functionality for connection health monitoring
- Singleton pattern for shared connections across components

### React Hook (`../hooks/useWebSocket.ts`)
- React hook for easy WebSocket integration in components
- Manages connection lifecycle automatically
- Provides callbacks for message handling and connection status changes
- Handles cleanup on component unmount

### Notification Manager (`notifications.ts`)
- Browser notification system for solar weather alerts
- Handles permission requests and notification display
- Different notification types for different alert severities
- Connection status notifications

### Connection Status Component (`../components/dashboard/ConnectionStatus.tsx`)
- Visual indicator of WebSocket connection status
- Shows connection details and error information
- Provides manual reconnection functionality
- Displays connection statistics

## Usage

### Basic WebSocket Connection
```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

function MyComponent() {
  const { isConnected, connectionStatus } = useWebSocket({
    onMessage: (message) => {
      if (message.type === 'alert') {
        // Handle real-time alert
        console.log('New alert:', message.data)
      }
    },
    onConnectionChange: (status) => {
      console.log('Connection status:', status)
    }
  })

  return (
    <div>
      Status: {isConnected ? 'Connected' : 'Disconnected'}
    </div>
  )
}
```

### Manual Connection Management
```typescript
import { getWebSocketClient } from '@/lib/websocket-client'

const client = getWebSocketClient()

// Connect manually
await client.connect()

// Send message
client.send({
  type: 'alert',
  data: { test: true }
})

// Listen for messages
const unsubscribe = client.onMessage((message) => {
  console.log('Received:', message)
})

// Disconnect
client.disconnect()
```

### Notifications
```typescript
import { getNotificationManager } from '@/lib/notifications'

const notificationManager = getNotificationManager()

// Request permission
await notificationManager.requestPermission()

// Show alert notification
notificationManager.showAlertNotification({
  severity: 'high',
  probability: 0.85,
  timestamp: new Date().toISOString(),
  message: 'Critical solar flare detected!'
})
```

## Features

### Real-time Updates
- Live solar weather data updates
- Automatic dashboard refresh when new data arrives
- Historical chart updates with new data points

### Connection Management
- Automatic reconnection on connection loss
- Exponential backoff with jitter for reconnection attempts
- Connection status indicators throughout the UI
- Manual reconnection capability

### Notifications
- Browser notifications for medium and high severity alerts
- Connection status notifications
- Configurable notification settings based on alert severity
- Silent notifications for low-priority events

### Error Handling
- Graceful degradation when WebSocket is unavailable
- Fallback to polling for data updates
- Comprehensive error logging and user feedback
- Retry mechanisms with configurable limits

## Configuration

### Environment Variables
- `NEXT_PUBLIC_WS_URL`: WebSocket server URL (defaults to API base URL)
- `NEXT_PUBLIC_API_BASE_URL`: API base URL for fallback WebSocket URL construction

### Connection Settings
- Reconnection interval: 5 seconds (with exponential backoff)
- Maximum reconnection attempts: 10
- Heartbeat interval: 30 seconds
- Connection timeout: 10 seconds

## Testing

The WebSocket integration includes comprehensive tests:

- Unit tests for WebSocket client functionality
- React hook testing with mock WebSocket
- Notification manager testing with mock browser APIs
- Integration tests for dashboard components

Run tests with:
```bash
npm test -- --testPathPattern="websocket|notifications"
```

## Architecture

The WebSocket integration follows these patterns:

1. **Singleton WebSocket Client**: Shared connection across all components
2. **React Hook Abstraction**: Easy integration with React components
3. **Event-driven Architecture**: Message handlers and status callbacks
4. **Graceful Degradation**: Fallback to HTTP polling when WebSocket unavailable
5. **Automatic Reconnection**: Resilient connection management
6. **Type Safety**: Full TypeScript support with proper message typing