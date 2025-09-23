#!/usr/bin/env python3
"""
ZERO-COMP API CLI Client

A command-line interface for testing and interacting with the ZERO-COMP Solar Weather API.
"""

import asyncio
import json
import sys
import argparse
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import aiohttp
import websockets
from pathlib import Path

# Configuration
DEFAULT_BASE_URL = "https://api.zero-comp.com"
DEFAULT_WS_URL = "wss://api.zero-comp.com/ws/alerts"


class ZeroCompAPIClient:
    """ZERO-COMP API client for CLI operations."""
    
    def __init__(self, base_url: str = DEFAULT_BASE_URL, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_current_alert(self) -> Dict[str, Any]:
        """Get current solar flare alert."""
        async with self.session.get(f"{self.base_url}/api/v1/alerts/current") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.json()
                raise Exception(f"API Error {response.status}: {error.get('message', 'Unknown error')}")
    
    async def get_alert_history(
        self,
        hours_back: int = 24,
        severity: Optional[str] = None,
        min_probability: Optional[float] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """Get historical alert data."""
        params = {
            'hours_back': hours_back,
            'page': page,
            'page_size': page_size
        }
        
        if severity:
            params['severity'] = severity
        if min_probability is not None:
            params['min_probability'] = min_probability
        
        async with self.session.get(f"{self.base_url}/api/v1/alerts/history", params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.json()
                raise Exception(f"API Error {response.status}: {error.get('message', 'Unknown error')}")
    
    async def get_alert_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get alert statistics."""
        params = {'hours_back': hours_back}
        
        async with self.session.get(f"{self.base_url}/api/v1/alerts/statistics", params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.json()
                raise Exception(f"API Error {response.status}: {error.get('message', 'Unknown error')}")
    
    async def export_csv(
        self,
        hours_back: int = 168,
        severity: Optional[str] = None,
        min_probability: Optional[float] = None,
        output_file: str = "solar_data.csv"
    ) -> str:
        """Export historical data as CSV."""
        params = {'hours_back': hours_back}
        
        if severity:
            params['severity'] = severity
        if min_probability is not None:
            params['min_probability'] = min_probability
        
        async with self.session.get(f"{self.base_url}/api/v1/alerts/export/csv", params=params) as response:
            if response.status == 200:
                content = await response.read()
                with open(output_file, 'wb') as f:
                    f.write(content)
                return output_file
            else:
                error = await response.json()
                raise Exception(f"API Error {response.status}: {error.get('message', 'Unknown error')}")
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        async with self.session.get(f"{self.base_url}/api/v1/users/profile") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.json()
                raise Exception(f"API Error {response.status}: {error.get('message', 'Unknown error')}")
    
    async def generate_api_key(self) -> Dict[str, Any]:
        """Generate a new API key."""
        async with self.session.post(f"{self.base_url}/api/v1/users/api-key") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.json()
                raise Exception(f"API Error {response.status}: {error.get('message', 'Unknown error')}")
    
    async def get_usage_stats(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get usage statistics."""
        params = {'hours_back': hours_back}
        
        async with self.session.get(f"{self.base_url}/api/v1/users/usage", params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.json()
                raise Exception(f"API Error {response.status}: {error.get('message', 'Unknown error')}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        async with self.session.get(f"{self.base_url}/health") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.json()
                raise Exception(f"API Error {response.status}: {error.get('message', 'Unknown error')}")


class WebSocketClient:
    """WebSocket client for real-time alerts."""
    
    def __init__(self, ws_url: str = DEFAULT_WS_URL, token: Optional[str] = None):
        self.ws_url = ws_url
        self.token = token
    
    async def connect_and_listen(self, duration: Optional[int] = None):
        """Connect to WebSocket and listen for alerts."""
        uri = f"{self.ws_url}?token={self.token}" if self.token else self.ws_url
        
        print(f"Connecting to {uri}")
        
        try:
            async with websockets.connect(uri) as websocket:
                print("✅ Connected to ZERO-COMP WebSocket")
                
                start_time = datetime.now()
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._handle_message(data)
                        
                        # Check duration limit
                        if duration and (datetime.now() - start_time).seconds >= duration:
                            print(f"\n⏰ Duration limit reached ({duration}s), disconnecting...")
                            break
                            
                    except json.JSONDecodeError:
                        print(f"❌ Invalid JSON received: {message}")
                    except KeyboardInterrupt:
                        print("\n👋 Disconnecting...")
                        break
                        
        except websockets.exceptions.ConnectionClosed:
            print("❌ Connection closed by server")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        msg_type = data.get('type', 'unknown')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        if msg_type == 'connection':
            print(f"🔗 [{timestamp}] Connection confirmed: {data.get('data', {}).get('message', '')}")
        
        elif msg_type == 'alert':
            alert_data = data.get('data', {})
            probability = alert_data.get('flare_probability', 0)
            severity = alert_data.get('severity_level', 'unknown')
            triggered = alert_data.get('alert_triggered', False)
            
            icon = "🚨" if triggered else "📊"
            print(f"{icon} [{timestamp}] Solar Flare Alert:")
            print(f"   Probability: {probability:.1%}")
            print(f"   Severity: {severity.upper()}")
            print(f"   Alert Triggered: {triggered}")
            print(f"   Message: {alert_data.get('message', '')}")
        
        elif msg_type == 'heartbeat':
            print(f"💓 [{timestamp}] Heartbeat")
        
        elif msg_type == 'error':
            error_data = data.get('data', {})
            print(f"❌ [{timestamp}] Error: {error_data.get('message', 'Unknown error')}")
        
        else:
            print(f"📨 [{timestamp}] {msg_type.upper()}: {json.dumps(data.get('data', {}), indent=2)}")


def load_config() -> Dict[str, Any]:
    """Load configuration from file or environment."""
    config = {
        'base_url': DEFAULT_BASE_URL,
        'ws_url': DEFAULT_WS_URL,
        'api_key': None
    }
    
    # Try to load from config file
    config_file = Path.home() / '.zerocomp' / 'config.json'
    if config_file.exists():
        try:
            with open(config_file) as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    # Override with environment variables
    import os
    if os.getenv('ZEROCOMP_API_KEY'):
        config['api_key'] = os.getenv('ZEROCOMP_API_KEY')
    if os.getenv('ZEROCOMP_BASE_URL'):
        config['base_url'] = os.getenv('ZEROCOMP_BASE_URL')
    
    return config


def save_config(config: Dict[str, Any]):
    """Save configuration to file."""
    config_dir = Path.home() / '.zerocomp'
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / 'config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Configuration saved to {config_file}")


def format_json_output(data: Any, indent: int = 2) -> str:
    """Format JSON data for pretty printing."""
    return json.dumps(data, indent=indent, default=str)


async def cmd_current(args):
    """Get current alert command."""
    config = load_config()
    
    async with ZeroCompAPIClient(config['base_url'], config['api_key']) as client:
        try:
            alert = await client.get_current_alert()
            
            if args.json:
                print(format_json_output(alert))
            else:
                print("🌞 Current Solar Flare Alert:")
                print(f"   Probability: {alert['current_probability']:.1%}")
                print(f"   Severity: {alert['severity_level'].upper()}")
                print(f"   Alert Active: {alert['alert_active']}")
                print(f"   Last Updated: {alert['last_updated']}")
                print(f"   Next Update: {alert['next_update']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


async def cmd_history(args):
    """Get alert history command."""
    config = load_config()
    
    async with ZeroCompAPIClient(config['base_url'], config['api_key']) as client:
        try:
            history = await client.get_alert_history(
                hours_back=args.hours,
                severity=args.severity,
                min_probability=args.min_probability,
                page=args.page,
                page_size=args.page_size
            )
            
            if args.json:
                print(format_json_output(history))
            else:
                alerts = history['alerts']
                print(f"📊 Solar Flare History ({len(alerts)} alerts, page {history['page']}):")
                print(f"   Total: {history['total_count']} alerts")
                print(f"   Has More: {history['has_more']}")
                print()
                
                for alert in alerts:
                    icon = "🚨" if alert['alert_triggered'] else "📊"
                    print(f"{icon} {alert['timestamp']}")
                    print(f"   Probability: {alert['flare_probability']:.1%}")
                    print(f"   Severity: {alert['severity_level'].upper()}")
                    print(f"   Message: {alert['message']}")
                    print()
                
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


async def cmd_stats(args):
    """Get statistics command."""
    config = load_config()
    
    async with ZeroCompAPIClient(config['base_url'], config['api_key']) as client:
        try:
            stats = await client.get_alert_statistics(hours_back=args.hours)
            
            if args.json:
                print(format_json_output(stats))
            else:
                print(f"📈 Solar Flare Statistics (last {args.hours} hours):")
                statistics = stats.get('statistics', {})
                
                for key, value in statistics.items():
                    if isinstance(value, float):
                        if 'probability' in key.lower():
                            print(f"   {key.replace('_', ' ').title()}: {value:.1%}")
                        else:
                            print(f"   {key.replace('_', ' ').title()}: {value:.2f}")
                    else:
                        print(f"   {key.replace('_', ' ').title()}: {value}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


async def cmd_export(args):
    """Export data command."""
    config = load_config()
    
    async with ZeroCompAPIClient(config['base_url'], config['api_key']) as client:
        try:
            filename = await client.export_csv(
                hours_back=args.hours,
                severity=args.severity,
                min_probability=args.min_probability,
                output_file=args.output
            )
            
            print(f"✅ Data exported to {filename}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


async def cmd_profile(args):
    """Get user profile command."""
    config = load_config()
    
    async with ZeroCompAPIClient(config['base_url'], config['api_key']) as client:
        try:
            profile = await client.get_user_profile()
            
            if args.json:
                print(format_json_output(profile))
            else:
                print("👤 User Profile:")
                print(f"   Email: {profile['email']}")
                print(f"   Subscription: {profile['subscription_tier'].upper()}")
                print(f"   API Key: {'✅ Active' if profile['api_key_exists'] else '❌ None'}")
                print(f"   Webhook: {profile.get('webhook_url', 'Not configured')}")
                print(f"   Created: {profile.get('created_at', 'Unknown')}")
                
                thresholds = profile.get('alert_thresholds', {})
                if thresholds:
                    print("   Alert Thresholds:")
                    for level, threshold in thresholds.items():
                        print(f"     {level.title()}: {threshold:.1%}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


async def cmd_usage(args):
    """Get usage statistics command."""
    config = load_config()
    
    async with ZeroCompAPIClient(config['base_url'], config['api_key']) as client:
        try:
            usage = await client.get_usage_stats(hours_back=args.hours)
            
            if args.json:
                print(format_json_output(usage))
            else:
                print(f"📊 Usage Statistics (last {args.hours} hours):")
                print(f"   Subscription Tier: {usage['subscription_tier'].upper()}")
                
                current = usage.get('current_period', {})
                for key, value in current.items():
                    print(f"   {key.replace('_', ' ').title()}: {value}")
                
                limits = usage.get('rate_limits', {})
                if limits:
                    print("   Rate Limits:")
                    for endpoint, limit in limits.items():
                        print(f"     {endpoint}: {limit}/hour")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


async def cmd_websocket(args):
    """WebSocket connection command."""
    config = load_config()
    
    client = WebSocketClient(config['ws_url'], config['api_key'])
    
    try:
        await client.connect_and_listen(duration=args.duration)
    except KeyboardInterrupt:
        print("\n👋 Disconnected")


async def cmd_health(args):
    """Health check command."""
    config = load_config()
    
    async with ZeroCompAPIClient(config['base_url'], config['api_key']) as client:
        try:
            health = await client.health_check()
            
            if args.json:
                print(format_json_output(health))
            else:
                print("🏥 API Health Check:")
                print(f"   Status: {health['status'].upper()}")
                print(f"   Service: {health['service']}")
                print(f"   Version: {health['version']}")
                print(f"   Environment: {health['environment']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


def cmd_config(args):
    """Configuration management command."""
    config = load_config()
    
    if args.set_api_key:
        config['api_key'] = args.set_api_key
        save_config(config)
        print("✅ API key updated")
    
    elif args.set_base_url:
        config['base_url'] = args.set_base_url
        save_config(config)
        print("✅ Base URL updated")
    
    else:
        print("⚙️  Current Configuration:")
        print(f"   Base URL: {config['base_url']}")
        print(f"   WebSocket URL: {config['ws_url']}")
        print(f"   API Key: {'✅ Set' if config['api_key'] else '❌ Not set'}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ZERO-COMP Solar Weather API CLI Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  zerocomp current                    # Get current alert
  zerocomp history --hours 48         # Get 48 hours of history
  zerocomp history --severity high    # Get high severity alerts only
  zerocomp export --hours 168         # Export 1 week of data
  zerocomp websocket --duration 60    # Listen to WebSocket for 60 seconds
  zerocomp config --set-api-key KEY   # Set API key
  
Environment Variables:
  ZEROCOMP_API_KEY     API key for authentication
  ZEROCOMP_BASE_URL    Base URL for API (default: https://api.zero-comp.com)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Current alert command
    current_parser = subparsers.add_parser('current', help='Get current solar flare alert')
    current_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Get historical alert data')
    history_parser.add_argument('--hours', type=int, default=24, help='Hours of history (default: 24)')
    history_parser.add_argument('--severity', choices=['low', 'medium', 'high'], help='Filter by severity')
    history_parser.add_argument('--min-probability', type=float, help='Minimum probability threshold')
    history_parser.add_argument('--page', type=int, default=1, help='Page number (default: 1)')
    history_parser.add_argument('--page-size', type=int, default=50, help='Page size (default: 50)')
    history_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Get alert statistics')
    stats_parser.add_argument('--hours', type=int, default=24, help='Hours to analyze (default: 24)')
    stats_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export historical data as CSV')
    export_parser.add_argument('--hours', type=int, default=168, help='Hours of data (default: 168)')
    export_parser.add_argument('--severity', choices=['low', 'medium', 'high'], help='Filter by severity')
    export_parser.add_argument('--min-probability', type=float, help='Minimum probability threshold')
    export_parser.add_argument('--output', default='solar_data.csv', help='Output filename')
    
    # Profile command
    profile_parser = subparsers.add_parser('profile', help='Get user profile')
    profile_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Usage command
    usage_parser = subparsers.add_parser('usage', help='Get usage statistics')
    usage_parser.add_argument('--hours', type=int, default=24, help='Hours to analyze (default: 24)')
    usage_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # WebSocket command
    ws_parser = subparsers.add_parser('websocket', help='Connect to WebSocket for real-time alerts')
    ws_parser.add_argument('--duration', type=int, help='Duration in seconds (default: unlimited)')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Check API health')
    health_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--set-api-key', help='Set API key')
    config_parser.add_argument('--set-base-url', help='Set base URL')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Command mapping
    commands = {
        'current': cmd_current,
        'history': cmd_history,
        'stats': cmd_stats,
        'export': cmd_export,
        'profile': cmd_profile,
        'usage': cmd_usage,
        'websocket': cmd_websocket,
        'health': cmd_health,
        'config': cmd_config
    }
    
    command_func = commands.get(args.command)
    if not command_func:
        print(f"❌ Unknown command: {args.command}")
        sys.exit(1)
    
    # Run async commands
    if args.command != 'config':
        try:
            asyncio.run(command_func(args))
        except KeyboardInterrupt:
            print("\n👋 Interrupted")
            sys.exit(0)
    else:
        command_func(args)


if __name__ == '__main__':
    main()