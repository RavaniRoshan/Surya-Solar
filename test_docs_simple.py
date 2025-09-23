#!/usr/bin/env python3
"""Simple test script for generated documentation."""

import json
from pathlib import Path

def test_documentation_files():
    """Test that all expected documentation files were generated."""
    
    docs_path = Path('docs/api')
    expected_files = [
        'api-reference.md',
        'authentication.md',
        'getting-started.md',
        'websockets.md',
        'error-handling.md',
        'openapi.json'
    ]
    
    print("🔍 Testing generated documentation files...")
    
    all_passed = True
    
    for filename in expected_files:
        file_path = docs_path / filename
        
        if not file_path.exists():
            print(f"❌ Missing file: {filename}")
            all_passed = False
            continue
            
        if file_path.stat().st_size == 0:
            print(f"❌ Empty file: {filename}")
            all_passed = False
            continue
            
        print(f"✅ {filename} - OK ({file_path.stat().st_size} bytes)")
    
    return all_passed


def test_openapi_schema():
    """Test the OpenAPI schema structure."""
    
    print("\n🔍 Testing OpenAPI schema...")
    
    schema_path = Path('docs/api/openapi.json')
    
    if not schema_path.exists():
        print("❌ OpenAPI schema file not found")
        return False
    
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Test required fields
        required_fields = ['openapi', 'info', 'paths', 'components']
        for field in required_fields:
            if field not in schema:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Test info section
        info = schema['info']
        if info['title'] != 'ZERO-COMP Solar Weather API':
            print(f"❌ Incorrect title: {info['title']}")
            return False
        
        # Test paths
        paths = schema['paths']
        expected_paths = ['/api/v1/alerts/current', '/api/v1/alerts/history', '/ws/alerts']
        for path in expected_paths:
            if path not in paths:
                print(f"❌ Missing path: {path}")
                return False
        
        # Test components
        components = schema['components']
        if 'securitySchemes' not in components:
            print("❌ Missing security schemes")
            return False
        
        if 'schemas' not in components:
            print("❌ Missing schemas")
            return False
        
        print("✅ OpenAPI schema structure is valid")
        print(f"✅ Found {len(paths)} API paths")
        print(f"✅ Found {len(components['schemas'])} data schemas")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in OpenAPI schema: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating OpenAPI schema: {e}")
        return False


def test_documentation_content():
    """Test that documentation files contain expected content."""
    
    print("\n🔍 Testing documentation content...")
    
    docs_path = Path('docs/api')
    
    # Test API reference
    api_ref_path = docs_path / 'api-reference.md'
    if api_ref_path.exists():
        content = api_ref_path.read_text(encoding='utf-8')
        if 'ZERO-COMP Solar Weather API Reference' in content:
            print("✅ API reference has correct title")
        else:
            print("❌ API reference missing title")
            return False
    
    # Test authentication guide
    auth_path = docs_path / 'authentication.md'
    if auth_path.exists():
        content = auth_path.read_text(encoding='utf-8')
        if 'JWT Tokens' in content and 'API Keys' in content:
            print("✅ Authentication guide has required sections")
        else:
            print("❌ Authentication guide missing required sections")
            return False
    
    # Test WebSocket documentation
    ws_path = docs_path / 'websockets.md'
    if ws_path.exists():
        content = ws_path.read_text(encoding='utf-8')
        if 'wss://api.zero-comp.com/ws/alerts' in content:
            print("✅ WebSocket documentation has correct endpoint")
        else:
            print("❌ WebSocket documentation missing endpoint")
            return False
    
    # Test getting started guide
    getting_started_path = docs_path / 'getting-started.md'
    if getting_started_path.exists():
        content = getting_started_path.read_text(encoding='utf-8')
        if 'Getting Started with ZERO-COMP API' in content:
            print("✅ Getting started guide has correct title")
        else:
            print("❌ Getting started guide missing title")
            return False
    
    # Test error handling guide
    error_path = docs_path / 'error-handling.md'
    if error_path.exists():
        content = error_path.read_text(encoding='utf-8')
        if 'Error Handling Guide' in content and '400 Bad Request' in content:
            print("✅ Error handling guide has required sections")
        else:
            print("❌ Error handling guide missing required sections")
            return False
    
    return True


def main():
    """Run all documentation tests."""
    
    print("🚀 Running documentation validation tests...\n")
    
    tests = [
        test_documentation_files,
        test_openapi_schema,
        test_documentation_content
    ]
    
    all_passed = True
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "="*50)
    
    if all_passed:
        print("🎉 All documentation tests passed!")
        print("📚 API documentation is ready for use")
    else:
        print("❌ Some documentation tests failed")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())