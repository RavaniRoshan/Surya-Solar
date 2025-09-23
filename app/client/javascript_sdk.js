/**
 * ZERO-COMP Solar Weather API JavaScript/Node.js SDK
 * 
 * A comprehensive JavaScript client library for the ZERO-COMP Solar Weather API.
 * Works in both browser and Node.js environments.
 */

// Check if we're in Node.js or browser environment
const isNode = typeof window === 'undefined';

// Import appropriate modules based on environment
let fetch, WebSocket;
if (isNode) {
    // Node.js environment
    try {
        fetch = require('node-fetch');
        WebSocket = require('ws');
    } catch (e) {
        console.warn('Optional dependencies not available:', e.message);
    }
} else {
    // Browser environment
    fetch = window.fetch;
    WebSocket = window.WebSocket;
}

/**
 * Solar flare severity levels
 */
const SeverityLevel = {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high'
};

/**
 * Subscription tier levels
 */
const SubscriptionTier = {
    FREE: 'free',
    PRO: 'pro',
    ENTERPRISE: 'enterprise'
};

/**
 * Base error class for ZERO-COMP API errors
 */
class ZeroCompAPIError extends Error {
    constructor(message, statusCode = null, errorCode = null, details = {}) {
        super(message);
        this.name = 'ZeroCompAPIError';
        this.statusCode = statusCode;
        this.errorCode = errorCode;
        this.details = details;
    }
}

/**
 * Rate limit exceeded error
 */
class RateLimitError extends ZeroCompAPIError {
    constructor(message, retryAfter = null, ...args) {
        super(message, ...args);
        this.name = 'RateLimitError';
        this.retryAfter = retryAfter;
    }
}

/**
 * Authentication error
 */
class AuthenticationError extends ZeroCompAPIError {
    constructor(message, ...args) {
        super(message, ...args);
        this.name = 'AuthenticationError';
    }
}

/**
 * Subscription tier insufficient error
 */
class SubscriptionError extends ZeroCompAPIError {
    constructor(message, ...args) {
        super(message, ...args);
        this.name = 'SubscriptionError';
    }
}

/**
 * Current alert data class
 */
class CurrentAlert {
    constructor(data) {
        this.currentProbability = data.current_probability;
        this.severityLevel = data.severity_level;
        this.lastUpdated = new Date(data.last_updated);
        this.nextUpdate = new Date(data.next_update);
        this.alertActive = data.alert_active;
    }
}

/**
 * Individual alert data point
 */
class AlertData {
    constructor(data) {
        this.id = data.id;
        this.timestamp = new Date(data.timestamp);
        this.flareProbability = data.flare_probability;
        this.severityLevel = data.severity_level;
        this.alertTriggered = data.alert_triggered;
        this.message = data.message;
    }
}

/**
 * Historical alerts response
 */
class HistoricalAlerts {
    constructor(data) {
        this.alerts = data.alerts.map(alert => new AlertData(alert));
        this.totalCount = data.total_count;
        this.page = data.page;
        this.pageSize = data.page_size;
        this.hasMore = data.has_more;
    }
}

/**
 * ZERO-COMP API Client
 */
class ZeroCompClient {
    /**
     * Initialize the ZERO-COMP API client
     * @param {Object} options - Configuration options
     * @param {string} options.apiKey - API key for authentication
     * @param {string} options.baseUrl - Base URL for the API
     * @param {number} options.timeout - Request timeout in milliseconds
     * @param {number} options.maxRetries - Maximum number of retries
     * @param {number} options.retryDelay - Delay between retries in milliseconds
     */
    constructor(options = {}) {
        this.apiKey = options.apiKey;
        this.baseUrl = (options.baseUrl || 'https://api.zero-comp.com').replace(/\/$/, '');
        this.timeout = options.timeout || 30000;
        this.maxRetries = options.maxRetries || 3;
        this.retryDelay = options.retryDelay || 1000;
    }

    /**
     * Get the current solar flare alert
     * @returns {Promise<CurrentAlert>} Current alert data
     */
    async getCurrentAlert() {
        // Implementation would go here
        throw new Error('Method not implemented');
    }

    /**
     * Get historical solar flare alert data
     * @param {Object} options - Query options
     * @returns {Promise<HistoricalAlerts>} Historical alert data
     */
    async getAlertHistory(options = {}) {
        // Implementation would go here
        throw new Error('Method not implemented');
    }
}

/**
 * WebSocket client for real-time solar flare alerts
 */
class ZeroCompWebSocketClient {
    /**
     * Initialize WebSocket client
     * @param {Object} options - Configuration options
     * @param {string} options.token - JWT token or API key for authentication
     * @param {string} options.wsUrl - WebSocket URL
     */
    constructor(options = {}) {
        this.token = options.token;
        this.wsUrl = options.wsUrl || 'wss://api.zero-comp.com/ws/alerts';
        this.websocket = null;
        this.listeners = new Map();
    }

    /**
     * Connect to the WebSocket
     * @returns {Promise<void>}
     */
    async connect() {
        // Implementation would go here
        throw new Error('Method not implemented');
    }

    /**
     * Add event listener
     * @param {string} event - Event type
     * @param {Function} callback - Callback function
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
}

// Convenience functions for quick usage

/**
 * Quick function to get current alert
 * @param {string} apiKey - API key for authentication
 * @returns {Promise<CurrentAlert>} Current alert data
 */
async function getCurrentAlert(apiKey) {
    const client = new ZeroCompClient({ apiKey });
    return await client.getCurrentAlert();
}

/**
 * Monitor real-time alerts with a callback function
 * @param {string} apiKey - API key for authentication
 * @param {Function} callback - Function to call when alert is received
 * @param {number} duration - Duration in milliseconds (null for unlimited)
 * @returns {Promise<void>}
 */
async function monitorAlerts(apiKey, callback, duration = null) {
    const wsClient = new ZeroCompWebSocketClient({ token: apiKey });
    
    wsClient.on('alert', callback);
    
    await wsClient.connect();
    
    if (duration) {
        setTimeout(() => {
            wsClient.disconnect();
        }, duration);
    }
    
    return wsClient;
}

// Export for different environments
if (isNode) {
    // Node.js exports
    module.exports = {
        ZeroCompClient,
        ZeroCompWebSocketClient,
        CurrentAlert,
        AlertData,
        HistoricalAlerts,
        SeverityLevel,
        SubscriptionTier,
        ZeroCompAPIError,
        RateLimitError,
        AuthenticationError,
        SubscriptionError,
        getCurrentAlert,
        monitorAlerts
    };
} else {
    // Browser globals
    window.ZeroComp = {
        ZeroCompClient,
        ZeroCompWebSocketClient,
        CurrentAlert,
        AlertData,
        HistoricalAlerts,
        SeverityLevel,
        SubscriptionTier,
        ZeroCompAPIError,
        RateLimitError,
        AuthenticationError,
        SubscriptionError,
        getCurrentAlert,
        monitorAlerts
    };
}

// Example usage
if (typeof window === 'undefined' && require.main === module) {
    // Node.js example
    (async () => {
        const client = new ZeroCompClient({ apiKey: 'your-api-key-here' });
        
        try {
            console.log('ZERO-COMP JavaScript SDK initialized');
            console.log('Client configuration:', {
                baseUrl: client.baseUrl,
                timeout: client.timeout,
                maxRetries: client.maxRetries
            });
            
        } catch (error) {
            console.error('SDK Error:', error.message);
        }
    })();
}