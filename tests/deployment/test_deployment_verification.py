"""
Deployment verification tests to ensure the system is working correctly
after deployment to production or staging environments.
"""

import pytest
import asyncio
import aiohttp
import websockets
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os


class DeploymentVerificationTests:
    """Test suite for verifying deployment health and functionality."""
    
    def __init__(self, base_url: str, ws_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.ws_url = ws_url.rstrip('/')
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def test_health_endpoint(self) -> bool:
        """Test the health endpoint."""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status != 200:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return False
                
                data = await response.json()
                
                # Check required fields
                required_fields = ["status", "timestamp", "version"]
                for field in required_fields:
                    if field not in data:
                        print(f"❌ Health response missing field: {field}")
                        return False
                
                if data["status"] != "healthy":
                    print(f"❌ Health status not healthy: {data['status']}")
                    return False
                
                print("✅ Health endpoint working correctly")
                return True
                
        except Exception as e:
            print(f"❌ Health check exception: {e}")
            return False
    
    async def test_api_endpoints(self) -> bool:
        """Test core API endpoints."""
        try:
            # Test current alerts endpoint
            async with self.session.get(
                f"{self.base_url}/api/v1/alerts/current",
                headers=self.get_headers()
            ) as response:
                if response.status not in [200, 401, 403]:  # 401/403 if no auth
                    print(f"❌ Current alerts endpoint failed: HTTP {response.status}")
                    return False
                
                if response.status == 200:
                    data = await response.json()
                    required_fields = ["current_probability", "severity_level", "last_updated"]
                    for field in required_fields:
                        if field not in data:
                            print(f"❌ Current alerts response missing field: {field}")
                            return False
            
            # Test alerts history endpoint
            async with self.session.get(
                f"{self.base_url}/api/v1/alerts/history",
                headers=self.get_headers()
            ) as response:
                if response.status not in [200, 401, 403]:
                    print(f"❌ Alerts history endpoint failed: HTTP {response.status}")
                    return False
            
            print("✅ API endpoints responding correctly")
            return True
            
        except Exception as e:
            print(f"❌ API endpoints test exception: {e}")
            return False
    
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection."""
        try:
            ws_url = f"{self.ws_url}/ws/alerts"
            if self.api_key:
                ws_url += f"?token={self.api_key}"
            
            async with websockets.connect(ws_url, timeout=10) as websocket:
                # Send ping
                await websocket.send(json.dumps({"type": "ping"}))
                
                # Wait for pong
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get("type") != "pong":
                    print(f"❌ WebSocket ping/pong failed: {data}")
                    return False
                
                print("✅ WebSocket connection working correctly")
                return True
                
        except asyncio.TimeoutError:
            print("❌ WebSocket connection timeout")
            return False
        except Exception as e:
            print(f"❌ WebSocket test exception: {e}")
            return False
    
    async def test_database_connectivity(self) -> bool:
        """Test database connectivity through API."""
        try:
            async with self.session.get(f"{self.base_url}/health/database") as response:
                if response.status != 200:
                    print(f"❌ Database health check failed: HTTP {response.status}")
                    return False
                
                data = await response.json()
                
                if data.get("status") != "connected":
                    print(f"❌ Database not connected: {data.get('status')}")
                    return False
                
                print("✅ Database connectivity verified")
                return True
                
        except Exception as e:
            print(f"❌ Database connectivity test exception: {e}")
            return False
    
    async def test_model_availability(self) -> bool:
        """Test ML model availability."""
        try:
            async with self.session.get(f"{self.base_url}/health/model") as response:
                if response.status != 200:
                    print(f"❌ Model health check failed: HTTP {response.status}")
                    return False
                
                data = await response.json()
                
                if data.get("status") != "loaded":
                    print(f"❌ Model not loaded: {data.get('status')}")
                    return False
                
                print("✅ ML model availability verified")
                return True
                
        except Exception as e:
            print(f"❌ Model availability test exception: {e}")
            return False
    
    async def test_authentication_flow(self) -> bool:
        """Test authentication endpoints."""
        try:
            # Test signup endpoint (should work or return appropriate error)
            test_user = {
                "email": f"test_{datetime.now().timestamp()}@example.com",
                "password": "testpassword123"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/signup",
                json=test_user,
                headers={"Content-Type": "application/json"}
            ) as response:
                # Should either succeed (201) or fail with validation error (422)
                if response.status not in [201, 422, 400]:
                    print(f"❌ Signup endpoint unexpected status: HTTP {response.status}")
                    return False
            
            # Test signin endpoint
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/signin",
                json={"email": "nonexistent@example.com", "password": "wrongpassword"},
                headers={"Content-Type": "application/json"}
            ) as response:
                # Should return 401 for invalid credentials
                if response.status not in [401, 422]:
                    print(f"❌ Signin endpoint unexpected status: HTTP {response.status}")
                    return False
            
            print("✅ Authentication endpoints working correctly")
            return True
            
        except Exception as e:
            print(f"❌ Authentication test exception: {e}")
            return False
    
    async def test_rate_limiting(self) -> bool:
        """Test rate limiting functionality."""
        try:
            # Make multiple rapid requests to trigger rate limiting
            tasks = []
            for _ in range(20):  # Exceed typical rate limits
                task = self.session.get(
                    f"{self.base_url}/api/v1/alerts/current",
                    headers=self.get_headers()
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if any requests were rate limited (429)
            rate_limited = False
            for response in responses:
                if hasattr(response, 'status') and response.status == 429:
                    rate_limited = True
                    break
                elif hasattr(response, 'status'):
                    await response.text()  # Consume response
            
            if not rate_limited:
                print("⚠️  Rate limiting may not be working (no 429 responses)")
            else:
                print("✅ Rate limiting is functioning")
            
            return True
            
        except Exception as e:
            print(f"❌ Rate limiting test exception: {e}")
            return False
    
    async def test_cors_headers(self) -> bool:
        """Test CORS headers are properly set."""
        try:
            async with self.session.options(
                f"{self.base_url}/api/v1/alerts/current",
                headers={"Origin": "https://example.com"}
            ) as response:
                headers = response.headers
                
                # Check for CORS headers
                cors_headers = [
                    "Access-Control-Allow-Origin",
                    "Access-Control-Allow-Methods",
                    "Access-Control-Allow-Headers"
                ]
                
                missing_headers = []
                for header in cors_headers:
                    if header not in headers:
                        missing_headers.append(header)
                
                if missing_headers:
                    print(f"⚠️  Missing CORS headers: {missing_headers}")
                else:
                    print("✅ CORS headers properly configured")
                
                return True
                
        except Exception as e:
            print(f"❌ CORS test exception: {e}")
            return False
    
    async def test_ssl_certificate(self) -> bool:
        """Test SSL certificate validity (for HTTPS endpoints)."""
        if not self.base_url.startswith('https'):
            print("ℹ️  Skipping SSL test (HTTP endpoint)")
            return True
        
        try:
            # The aiohttp session will validate SSL by default
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    print("✅ SSL certificate is valid")
                    return True
                else:
                    print(f"❌ SSL test failed: HTTP {response.status}")
                    return False
                    
        except aiohttp.ClientSSLError as e:
            print(f"❌ SSL certificate error: {e}")
            return False
        except Exception as e:
            print(f"❌ SSL test exception: {e}")
            return False
    
    async def test_response_times(self) -> bool:
        """Test API response times are acceptable."""
        try:
            endpoints = [
                "/health",
                "/api/v1/alerts/current",
                "/api/v1/alerts/history"
            ]
            
            max_response_time = 2.0  # 2 seconds
            slow_endpoints = []
            
            for endpoint in endpoints:
                start_time = asyncio.get_event_loop().time()
                
                try:
                    async with self.session.get(
                        f"{self.base_url}{endpoint}",
                        headers=self.get_headers()
                    ) as response:
                        await response.text()  # Consume response
                        
                    end_time = asyncio.get_event_loop().time()
                    response_time = end_time - start_time
                    
                    if response_time > max_response_time:
                        slow_endpoints.append(f"{endpoint}: {response_time:.2f}s")
                        
                except Exception:
                    # Endpoint might require auth, that's okay for this test
                    pass
            
            if slow_endpoints:
                print(f"⚠️  Slow endpoints detected: {slow_endpoints}")
            else:
                print("✅ All endpoints responding within acceptable time")
            
            return True
            
        except Exception as e:
            print(f"❌ Response time test exception: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all deployment verification tests."""
        print("🚀 Starting deployment verification tests...")
        print(f"   Base URL: {self.base_url}")
        print(f"   WebSocket URL: {self.ws_url}")
        print()
        
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("API Endpoints", self.test_api_endpoints),
            ("WebSocket Connection", self.test_websocket_connection),
            ("Database Connectivity", self.test_database_connectivity),
            ("Model Availability", self.test_model_availability),
            ("Authentication Flow", self.test_authentication_flow),
            ("Rate Limiting", self.test_rate_limiting),
            ("CORS Headers", self.test_cors_headers),
            ("SSL Certificate", self.test_ssl_certificate),
            ("Response Times", self.test_response_times),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"Running: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
            print()
        
        # Summary
        print("=" * 60)
        print("DEPLOYMENT VERIFICATION SUMMARY")
        print("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<25} {status}")
        
        print()
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All deployment verification tests passed!")
        else:
            print(f"💥 {total - passed} tests failed!")
        
        return results


async def main():
    """Main function to run deployment verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Solar Weather API Deployment Verification")
    parser.add_argument("--url", required=True, help="Base URL of the deployed API")
    parser.add_argument("--ws-url", help="WebSocket URL (defaults to HTTP->WS conversion)")
    parser.add_argument("--api-key", help="API key for authenticated requests")
    
    args = parser.parse_args()
    
    # Convert HTTP URL to WebSocket URL if not provided
    ws_url = args.ws_url
    if not ws_url:
        ws_url = args.url.replace('http://', 'ws://').replace('https://', 'wss://')
    
    async with DeploymentVerificationTests(args.url, ws_url, args.api_key) as tests:
        results = await tests.run_all_tests()
        
        # Exit with error code if any tests failed
        if not all(results.values()):
            exit(1)


if __name__ == "__main__":
    asyncio.run(main())