#!/usr/bin/env python3
"""
ZERO-COMP Python SDK Examples

This file demonstrates various usage patterns for the ZERO-COMP Solar Weather API Python SDK.
"""

import asyncio
import os
from datetime import datetime, timedelta
from app.client.python_sdk import (
    ZeroCompClient, AsyncZeroCompClient, WebSocketClient,
    SeverityLevel, SubscriptionTier,
    ZeroCompAPIError, AuthenticationError, RateLimitError, SubscriptionError,
    get_current_alert, get_current_alert_async, monitor_alerts
)


def example_basic_usage():
    """Basic synchronous usage example."""
    print("=== Basic Synchronous Usage ===")
    
    # Initialize client with API key
    api_key = os.getenv('ZEROCOMP_API_KEY', 'your-api-key-here')
    client = ZeroCompClient(api_key=api_key)
    
    try:
        # Get current alert
        alert = client.get_current_alert()
        print(f"Current solar flare probability: {alert.current_probability:.1%}")
        print(f"Severity level: {alert.severity_level.value}")
        print(f"Alert active: {alert.alert_active}")
        print(f"Last updated: {alert.last_updated}")
        print(f"Next update: {alert.next_update}")
        
    except AuthenticationError:
        print("❌ Authentication failed - check your API key")
    except RateLimitError as e:
        print(f"❌ Rate limit exceeded - retry after {e.retry_after} seconds")
    except ZeroCompAPIError as e:
        print(f"❌ API Error: {e}")


async def example_async_usage():
    """Asynchronous usage example."""
    print("\n=== Asynchronous Usage ===")
    
    api_key = os.getenv('ZEROCOMP_API_KEY', 'your-api-key-here')
    
    async with AsyncZeroCompClient(api_key=api_key) as client:
        try:
            # Get current alert
            alert = await client.get_current_alert()
            print(f"Current probability: {alert.current_probability:.1%}")
            
            # Get historical data
            history = await client.get_alert_history(
                hours_back=48,
                severity=SeverityLevel.HIGH,
                page_size=10
            )
            print(f"High-severity alerts in last 48 hours: {len(history.alerts)}")
            
            # Get statistics
            stats = await client.get_alert_statistics(hours_back=24)
            print(f"Statistics: {stats}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


def example_historical_data():
    """Historical data retrieval example."""
    print("\n=== Historical Data Retrieval ===")
    
    api_key = os.getenv('ZEROCOMP_API_KEY', 'your-api-key-here')
    client = ZeroCompClient(api_key=api_key)
    
    try:
        # Get last 7 days of high-severity alerts
        history = client.get_alert_history(
            hours_back=168,  # 7 days
            severity=SeverityLevel.HIGH,
            min_probability=0.7,
            page_size=100
        )
        
        print(f"Found {len(history.alerts)} high-severity alerts (>70% probability)")
        print(f"Total alerts in database: {history.total_count}")
        print(f"Has more pages: {history.has_more}")
        
        # Display recent alerts
        for alert in history.alerts[:5]:
            print(f"  {alert.timestamp}: {alert.flare_probability:.1%} ({alert.severity_level.value})")
            
    except SubscriptionError:
        print("❌ This feature requires Pro or Enterprise subscription")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_csv_export():
    """CSV export example (Enterprise feature)."""
    print("\n=== CSV Export (Enterprise) ===")
    
    api_key = os.getenv('ZEROCOMP_API_KEY', 'your-api-key-here')
    client = ZeroCompClient(api_key=api_key)
    
    try:
        # Export last month of data
        csv_data = client.export_csv(
            hours_back=720,  # 30 days
            min_probability=0.5
        )
        
        # Save to file
        filename = f"solar_data_{datetime.now().strftime('%Y%m%d')}.csv"
        with open(filename, 'wb') as f:
            f.write(csv_data)
        
        print(f"✅ Data exported to {filename}")
        print(f"File size: {len(csv_data)} bytes")
        
    except SubscriptionError:
        print("❌ CSV export requires Enterprise subscription")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_user_management():
    """User profile and API key management example."""
    print("\n=== User Management ===")
    
    api_key = os.getenv('ZEROCOMP_API_KEY', 'your-api-key-here')
    client = ZeroCompClient(api_key=api_key)
    
    try:
        # Get user profile
        profile = client.get_user_profile()
        print(f"Email: {profile.email}")
        print(f"Subscription: {profile.subscription_tier.value}")
        print(f"API key exists: {profile.api_key_exists}")
        print(f"Webhook URL: {profile.webhook_url or 'Not configured'}")
        
        # Update profile settings
        updated_profile = client.update_profile(
            webhook_url="https://your-app.com/webhooks/solar-alerts",
            alert_thresholds={
                "low": 0.3,
                "medium": 0.6,
                "high": 0.8
            }
        )
        print(f"✅ Profile updated")
        
        # Get usage statistics
        usage = client.get_usage_statistics(hours_back=24)
        print(f"API calls in last 24h: {usage}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_websocket_monitoring():
    """WebSocket real-time monitoring example."""
    print("\n=== WebSocket Real-time Monitoring ===")
    
    api_key = os.getenv('ZEROCOMP_API_KEY', 'your-api-key-here')
    
    try:
        async with WebSocketClient(token=api_key) as ws:
            print("🔗 Connected to ZERO-COMP WebSocket")
            
            # Listen for 30 seconds
            start_time = datetime.now()
            timeout = timedelta(seconds=30)
            
            async for message in ws.listen():
                print(f"📨 Received: {message}")
                
                if message.get('type') == 'alert':
                    alert_data = message['data']
                    probability = alert_data.get('flare_probability', 0)
                    severity = alert_data.get('severity_level', 'unknown')
                    
                    if alert_data.get('alert_triggered'):
                        print(f"🚨 ALERT: {probability:.1%} probability ({severity})")
                    else:
                        print(f"📊 Update: {probability:.1%} probability ({severity})")
                
                # Break after timeout
                if datetime.now() - start_time > timeout:
                    print("⏰ Timeout reached, disconnecting...")
                    break
                    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


def example_error_handling():
    """Comprehensive error handling example."""
    print("\n=== Error Handling ===")
    
    # Test with invalid API key
    client = ZeroCompClient(api_key="invalid-key")
    
    try:
        alert = client.get_current_alert()
        print(f"Alert: {alert}")
        
    except AuthenticationError as e:
        print(f"🔐 Authentication Error: {e.message}")
        print(f"   Status Code: {e.status_code}")
        print(f"   Error Code: {e.error_code}")
        
    except RateLimitError as e:
        print(f"⏱️ Rate Limit Error: {e.message}")
        print(f"   Retry After: {e.retry_after} seconds")
        print(f"   Details: {e.details}")
        
    except SubscriptionError as e:
        print(f"💳 Subscription Error: {e.message}")
        print(f"   Required Tier: {e.details.get('required_tier', 'Unknown')}")
        
    except ZeroCompAPIError as e:
        print(f"🌐 API Error: {e.message}")
        print(f"   Status Code: {e.status_code}")
        print(f"   Error Code: {e.error_code}")
        print(f"   Details: {e.details}")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


def example_convenience_functions():
    """Convenience functions example."""
    print("\n=== Convenience Functions ===")
    
    api_key = os.getenv('ZEROCOMP_API_KEY', 'your-api-key-here')
    
    try:
        # Quick synchronous call
        alert = get_current_alert(api_key)
        print(f"Quick sync call: {alert.current_probability:.1%}")
        
    except Exception as e:
        print(f"❌ Sync error: {e}")


async def example_async_convenience():
    """Async convenience functions example."""
    api_key = os.getenv('ZEROCOMP_API_KEY', 'your-api-key-here')
    
    try:
        # Quick asynchronous call
        alert = await get_current_alert_async(api_key)
        print(f"Quick async call: {alert.current_probability:.1%}")
        
    except Exception as e:
        print(f"❌ Async error: {e}")


def example_monitoring_callback():
    """Monitoring with callback function example."""
    print("\n=== Monitoring with Callback ===")
    
    def alert_callback(alert_data):
        """Callback function for processing alerts."""
        probability = alert_data.get('flare_probability', 0)
        severity = alert_data.get('severity_level', 'unknown')
        triggered = alert_data.get('alert_triggered', False)
        
        if triggered:
            print(f"🚨 CALLBACK ALERT: {probability:.1%} ({severity})")
            # Here you could send notifications, update databases, etc.
        else:
            print(f"📊 CALLBACK UPDATE: {probability:.1%} ({severity})")
    
    api_key = os.getenv('ZEROCOMP_API_KEY', 'your-api-key-here')
    
    try:
        # Monitor for 15 seconds
        print("🎧 Starting callback monitoring for 15 seconds...")
        monitor_alerts(api_key, alert_callback, duration=15)
        print("✅ Monitoring completed")
        
    except Exception as e:
        print(f"❌ Monitoring error: {e}")


async def example_batch_operations():
    """Batch operations example."""
    print("\n=== Batch Operations ===")
    
    api_key = os.getenv('ZEROCOMP_API_KEY', 'your-api-key-here')
    
    async with AsyncZeroCompClient(api_key=api_key) as client:
        try:
            # Perform multiple operations concurrently
            tasks = [
                client.get_current_alert(),
                client.get_alert_history(hours_back=24),
                client.get_alert_statistics(hours_back=24),
                client.get_user_profile(),
                client.get_usage_statistics(hours_back=24)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            current_alert, history, stats, profile, usage = results
            
            print("📊 Batch Results:")
            if not isinstance(current_alert, Exception):
                print(f"   Current: {current_alert.current_probability:.1%}")
            if not isinstance(history, Exception):
                print(f"   History: {len(history.alerts)} alerts")
            if not isinstance(profile, Exception):
                print(f"   Profile: {profile.subscription_tier.value}")
            
        except Exception as e:
            print(f"❌ Batch error: {e}")


def main():
    """Run all examples."""
    print("🌞 ZERO-COMP Python SDK Examples")
    print("=" * 50)
    
    # Synchronous examples
    example_basic_usage()
    example_historical_data()
    example_csv_export()
    example_user_management()
    example_error_handling()
    example_convenience_functions()
    example_monitoring_callback()
    
    # Asynchronous examples
    asyncio.run(example_async_usage())
    asyncio.run(example_websocket_monitoring())
    asyncio.run(example_async_convenience())
    asyncio.run(example_batch_operations())
    
    print("\n✅ All examples completed!")


if __name__ == "__main__":
    main()