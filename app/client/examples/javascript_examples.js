/**
 * ZERO-COMP JavaScript SDK Examples
 * 
 * This file demonstrates various usage patterns for the ZERO-COMP Solar Weather API JavaScript SDK.
 * Works in both Node.js and browser environments.
 */

// Import the SDK (adjust path as needed)
const {
    ZeroCompClient,
    ZeroCompWebSocketClient,
    SeverityLevel,
    SubscriptionTier,
    ZeroCompAPIError,
    AuthenticationError,
    RateLimitError,
    SubscriptionError,
    getCurrentAlert,
    monitorAlerts
} = require('../javascript_sdk');

/**
 * Basic usage example
 */
async function exampleBasicUsage() {
    console.log('=== Basic Usage ===');
    
    // Initialize client with API key
    const apiKey = process.env.ZEROCOMP_API_KEY || 'your-api-key-here';
    const client = new ZeroCompClient({ apiKey });
    
    try {
        // Get current alert
        const alert = await client.getCurrentAlert();
        console.log(`Current solar flare probability: ${(alert.currentProbability * 100).toFixed(1)}%`);
        console.log(`Severity level: ${alert.severityLevel}`);
        console.log(`Alert active: ${alert.alertActive}`);
        console.log(`Last updated: ${alert.lastUpdated}`);
        console.log(`Next update: ${alert.nextUpdate}`);
        
    } catch (error) {
        if (error instanceof AuthenticationError) {
            console.log('❌ Authentication failed - check your API key');
        } else if (error instanceof RateLimitError) {
            console.log(`❌ Rate limit exceeded - retry after ${error.retryAfter} seconds`);
        } else {
            console.log(`❌ API Error: ${error.message}`);
        }
    }
}

/**
 * Historical data retrieval example
 */
async function exampleHistoricalData() {
    console.log('\n=== Historical Data Retrieval ===');
    
    const apiKey = process.env.ZEROCOMP_API_KEY || 'your-api-key-here';
    const client = new ZeroCompClient({ apiKey });
    
    try {
        // Get last 7 days of high-severity alerts
        const history = await client.getAlertHistory({
            hoursBack: 168, // 7 days
            severity: SeverityLevel.HIGH,
            minProbability: 0.7,
            pageSize: 100
        });
        
        console.log(`Found ${history.alerts.length} high-severity alerts (>70% probability)`);
        console.log(`Total alerts in database: ${history.totalCount}`);
        console.log(`Has more pages: ${history.hasMore}`);
        
        // Display recent alerts
        history.alerts.slice(0, 5).forEach(alert => {
            console.log(`  ${alert.timestamp.toISOString()}: ${(alert.flareProbability * 100).toFixed(1)}% (${alert.severityLevel})`);
        });
        
    } catch (error) {
        if (error instanceof SubscriptionError) {
            console.log('❌ This feature requires Pro or Enterprise subscription');
        } else {
            console.log(`❌ Error: ${error.message}`);
        }
    }
}

/**
 * CSV export example (Enterprise feature)
 */
async function exampleCsvExport() {
    console.log('\n=== CSV Export (Enterprise) ===');
    
    const apiKey = process.env.ZEROCOMP_API_KEY || 'your-api-key-here';
    const client = new ZeroCompClient({ apiKey });
    
    try {
        // Export last month of data
        const csvData = await client.exportCsv({
            hoursBack: 720, // 30 days
            minProbability: 0.5
        });
        
        // Save to file (Node.js only)
        if (typeof require !== 'undefined') {
            const fs = require('fs');
            const filename = `solar_data_${new Date().toISOString().split('T')[0]}.csv`;
            fs.writeFileSync(filename, csvData);
            console.log(`✅ Data exported to ${filename}`);
            console.log(`File size: ${csvData.length} bytes`);
        } else {
            // Browser - create download link
            const blob = csvData;
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `solar_data_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            URL.revokeObjectURL(url);
            console.log('✅ CSV download initiated');
        }
        
    } catch (error) {
        if (error instanceof SubscriptionError) {
            console.log('❌ CSV export requires Enterprise subscription');
        } else {
            console.log(`❌ Error: ${error.message}`);
        }
    }
}

/**
 * User profile and management example
 */
async function exampleUserManagement() {
    console.log('\n=== User Management ===');
    
    const apiKey = process.env.ZEROCOMP_API_KEY || 'your-api-key-here';
    const client = new ZeroCompClient({ apiKey });
    
    try {
        // Get user profile
        const profile = await client.getUserProfile();
        console.log(`Email: ${profile.email}`);
        console.log(`Subscription: ${profile.subscriptionTier}`);
        console.log(`API key exists: ${profile.apiKeyExists}`);
        console.log(`Webhook URL: ${profile.webhookUrl || 'Not configured'}`);
        
        // Update profile settings
        const updatedProfile = await client.updateProfile({
            webhookUrl: 'https://your-app.com/webhooks/solar-alerts',
            alertThresholds: {
                low: 0.3,
                medium: 0.6,
                high: 0.8
            }
        });
        console.log('✅ Profile updated');
        
        // Get usage statistics
        const usage = await client.getUsageStatistics(24);
        console.log('Usage stats:', usage);
        
    } catch (error) {
        console.log(`❌ Error: ${error.message}`);
    }
}

/**
 * WebSocket real-time monitoring example
 */
async function exampleWebSocketMonitoring() {
    console.log('\n=== WebSocket Real-time Monitoring ===');
    
    const apiKey = process.env.ZEROCOMP_API_KEY || 'your-api-key-here';
    const wsClient = new ZeroCompWebSocketClient({ token: apiKey });
    
    try {
        // Set up event listeners
        wsClient.on('connection', (data) => {
            console.log('🔗 Connected to ZERO-COMP WebSocket');
        });
        
        wsClient.on('alert', (data) => {
            const alertData = data.data;
            const probability = alertData.flare_probability || 0;
            const severity = alertData.severity_level || 'unknown';
            
            if (alertData.alert_triggered) {
                console.log(`🚨 ALERT: ${(probability * 100).toFixed(1)}% probability (${severity})`);
            } else {
                console.log(`📊 Update: ${(probability * 100).toFixed(1)}% probability (${severity})`);
            }
        });
        
        wsClient.on('heartbeat', (data) => {
            console.log('💓 Heartbeat');
        });
        
        wsClient.on('error', (data) => {
            console.log(`❌ WebSocket Error: ${data.data.message}`);
        });
        
        // Connect and listen for 30 seconds
        await wsClient.connect();
        
        setTimeout(() => {
            console.log('⏰ Timeout reached, disconnecting...');
            wsClient.disconnect();
        }, 30000);
        
    } catch (error) {
        console.log(`❌ WebSocket error: ${error.message}`);
    }
}

/**
 * Comprehensive error handling example
 */
async function exampleErrorHandling() {
    console.log('\n=== Error Handling ===');
    
    // Test with invalid API key
    const client = new ZeroCompClient({ apiKey: 'invalid-key' });
    
    try {
        const alert = await client.getCurrentAlert();
        console.log(`Alert: ${alert}`);
        
    } catch (error) {
        if (error instanceof AuthenticationError) {
            console.log(`🔐 Authentication Error: ${error.message}`);
            console.log(`   Status Code: ${error.statusCode}`);
            console.log(`   Error Code: ${error.errorCode}`);
            
        } else if (error instanceof RateLimitError) {
            console.log(`⏱️ Rate Limit Error: ${error.message}`);
            console.log(`   Retry After: ${error.retryAfter} seconds`);
            console.log(`   Details:`, error.details);
            
        } else if (error instanceof SubscriptionError) {
            console.log(`💳 Subscription Error: ${error.message}`);
            console.log(`   Required Tier: ${error.details?.required_tier || 'Unknown'}`);
            
        } else if (error instanceof ZeroCompAPIError) {
            console.log(`🌐 API Error: ${error.message}`);
            console.log(`   Status Code: ${error.statusCode}`);
            console.log(`   Error Code: ${error.errorCode}`);
            console.log(`   Details:`, error.details);
            
        } else {
            console.log(`❌ Unexpected Error: ${error.message}`);
        }
    }
}

/**
 * Convenience functions example
 */
async function exampleConvenienceFunctions() {
    console.log('\n=== Convenience Functions ===');
    
    const apiKey = process.env.ZEROCOMP_API_KEY || 'your-api-key-here';
    
    try {
        // Quick function call
        const alert = await getCurrentAlert(apiKey);
        console.log(`Quick call: ${(alert.currentProbability * 100).toFixed(1)}%`);
        
    } catch (error) {
        console.log(`❌ Error: ${error.message}`);
    }
}

/**
 * Monitoring with callback function example
 */
async function exampleMonitoringCallback() {
    console.log('\n=== Monitoring with Callback ===');
    
    const alertCallback = (alertData) => {
        const data = alertData.data;
        const probability = data.flare_probability || 0;
        const severity = data.severity_level || 'unknown';
        const triggered = data.alert_triggered || false;
        
        if (triggered) {
            console.log(`🚨 CALLBACK ALERT: ${(probability * 100).toFixed(1)}% (${severity})`);
            // Here you could send notifications, update databases, etc.
        } else {
            console.log(`📊 CALLBACK UPDATE: ${(probability * 100).toFixed(1)}% (${severity})`);
        }
    };
    
    const apiKey = process.env.ZEROCOMP_API_KEY || 'your-api-key-here';
    
    try {
        // Monitor for 15 seconds
        console.log('🎧 Starting callback monitoring for 15 seconds...');
        const wsClient = await monitorAlerts(apiKey, alertCallback, 15000);
        
        // Wait for monitoring to complete
        setTimeout(() => {
            console.log('✅ Monitoring completed');
        }, 16000);
        
    } catch (error) {
        console.log(`❌ Monitoring error: ${error.message}`);
    }
}

/**
 * Batch operations example using Promise.all
 */
async function exampleBatchOperations() {
    console.log('\n=== Batch Operations ===');
    
    const apiKey = process.env.ZEROCOMP_API_KEY || 'your-api-key-here';
    const client = new ZeroCompClient({ apiKey });
    
    try {
        // Perform multiple operations concurrently
        const [currentAlert, history, stats, profile, usage] = await Promise.allSettled([
            client.getCurrentAlert(),
            client.getAlertHistory({ hoursBack: 24 }),
            client.getAlertStatistics(24),
            client.getUserProfile(),
            client.getUsageStatistics(24)
        ]);
        
        console.log('📊 Batch Results:');
        
        if (currentAlert.status === 'fulfilled') {
            console.log(`   Current: ${(currentAlert.value.currentProbability * 100).toFixed(1)}%`);
        }
        
        if (history.status === 'fulfilled') {
            console.log(`   History: ${history.value.alerts.length} alerts`);
        }
        
        if (profile.status === 'fulfilled') {
            console.log(`   Profile: ${profile.value.subscriptionTier}`);
        }
        
        // Log any errors
        [currentAlert, history, stats, profile, usage].forEach((result, index) => {
            if (result.status === 'rejected') {
                console.log(`   Error in operation ${index}: ${result.reason.message}`);
            }
        });
        
    } catch (error) {
        console.log(`❌ Batch error: ${error.message}`);
    }
}

/**
 * Browser-specific example (for when running in browser)
 */
function exampleBrowserIntegration() {
    console.log('\n=== Browser Integration Example ===');
    
    if (typeof window === 'undefined') {
        console.log('⚠️ This example is for browser environments only');
        return;
    }
    
    // Example of integrating with a web page
    const apiKey = 'your-api-key-here';
    const client = new ZeroComp.ZeroCompClient({ apiKey });
    
    // Update dashboard every 10 minutes
    async function updateDashboard() {
        try {
            const alert = await client.getCurrentAlert();
            
            // Update DOM elements
            document.getElementById('probability').textContent = 
                `${(alert.currentProbability * 100).toFixed(1)}%`;
            document.getElementById('severity').textContent = alert.severityLevel;
            document.getElementById('alert-status').textContent = 
                alert.alertActive ? 'ACTIVE' : 'NORMAL';
            
            // Update chart or other visualizations
            updateChart(alert);
            
        } catch (error) {
            console.error('Dashboard update failed:', error);
            document.getElementById('error-message').textContent = error.message;
        }
    }
    
    // Set up real-time WebSocket connection
    const wsClient = new ZeroComp.ZeroCompWebSocketClient({ token: apiKey });
    
    wsClient.on('alert', (data) => {
        const alertData = data.data;
        
        // Show browser notification for high-severity alerts
        if (alertData.alert_triggered && alertData.severity_level === 'high') {
            if (Notification.permission === 'granted') {
                new Notification('Solar Flare Alert!', {
                    body: `High probability solar flare detected: ${(alertData.flare_probability * 100).toFixed(1)}%`,
                    icon: '/icons/solar-flare.png'
                });
            }
        }
        
        // Update real-time display
        updateDashboard();
    });
    
    // Initialize
    wsClient.connect();
    updateDashboard();
    setInterval(updateDashboard, 10 * 60 * 1000); // Every 10 minutes
    
    function updateChart(alert) {
        // Placeholder for chart update logic
        console.log('Updating chart with new data:', alert);
    }
}

/**
 * Run all examples
 */
async function main() {
    console.log('🌞 ZERO-COMP JavaScript SDK Examples');
    console.log('='.repeat(50));
    
    try {
        await exampleBasicUsage();
        await exampleHistoricalData();
        await exampleCsvExport();
        await exampleUserManagement();
        await exampleErrorHandling();
        await exampleConvenienceFunctions();
        await exampleBatchOperations();
        
        // WebSocket examples (run with timeout)
        const wsPromise1 = exampleWebSocketMonitoring();
        const wsPromise2 = exampleMonitoringCallback();
        
        await Promise.race([
            wsPromise1,
            new Promise(resolve => setTimeout(resolve, 35000))
        ]);
        
        await Promise.race([
            wsPromise2,
            new Promise(resolve => setTimeout(resolve, 20000))
        ]);
        
        // Browser example (only shows code, doesn't run)
        exampleBrowserIntegration();
        
        console.log('\n✅ All examples completed!');
        
    } catch (error) {
        console.error('❌ Example execution failed:', error);
    }
}

// Export for different environments
if (typeof module !== 'undefined' && module.exports) {
    // Node.js
    module.exports = {
        exampleBasicUsage,
        exampleHistoricalData,
        exampleCsvExport,
        exampleUserManagement,
        exampleWebSocketMonitoring,
        exampleErrorHandling,
        exampleConvenienceFunctions,
        exampleMonitoringCallback,
        exampleBatchOperations,
        exampleBrowserIntegration,
        main
    };
    
    // Run examples if this file is executed directly
    if (require.main === module) {
        main().catch(console.error);
    }
} else {
    // Browser
    window.ZeroCompExamples = {
        exampleBasicUsage,
        exampleHistoricalData,
        exampleCsvExport,
        exampleUserManagement,
        exampleWebSocketMonitoring,
        exampleErrorHandling,
        exampleConvenienceFunctions,
        exampleMonitoringCallback,
        exampleBatchOperations,
        exampleBrowserIntegration,
        main
    };
}