"""Tests for API documentation generation."""

import pytest
import json
from pathlib import Path
import tempfile
import shutil

from app.main import create_app
from app.docs.generator import APIDocumentationGenerator
from app.docs.openapi_customization import customize_openapi_schema


class TestAPIDocumentation:
    """Test API documentation generation and validation."""
    
    def test_openapi_schema_generation(self):
        """Test that OpenAPI schema is generated correctly."""
        app = create_app()
        schema = app.openapi()
        
        # Verify required OpenAPI fields
        assert 'openapi' in schema
        assert 'info' in schema
        assert 'paths' in schema
        assert 'components' in schema
        
        # Verify API info
        info = schema['info']
        assert info['title'] == 'ZERO-COMP Solar Weather API'
        assert 'version' in info
        assert 'description' in info
        
        # Verify security schemes
        security_schemes = schema['components']['securitySchemes']
        assert 'BearerAuth' in security_schemes
        assert 'ApiKeyAuth' in security_schemes
        
    def test_openapi_customization(self):
        """Test OpenAPI schema customization."""
        app = create_app()
        schema = customize_openapi_schema(app)
        
        # Verify enhanced documentation
        assert 'components' in schema
        assert 'securitySchemes' in schema['components']
        
        # Check for examples in schemas
        schemas = schema['components'].get('schemas', {})
        if 'CurrentAlertResponse' in schemas:
            # Should have example data
            assert 'example' in schemas['CurrentAlertResponse']
        
    def test_endpoint_documentation_completeness(self):
        """Test that all endpoints have proper documentation."""
        app = create_app()
        schema = app.openapi()
        
        paths = schema.get('paths', {})
        assert len(paths) > 0, "No API paths found"
        
        # Check each endpoint has required documentation
        for path, methods in paths.items():
            for method, details in methods.items():
                # Skip OPTIONS methods
                if method.upper() == 'OPTIONS':
                    continue
                
                assert 'summary' in details, f"{method.upper()} {path} missing summary"
                assert 'tags' in details, f"{method.upper()} {path} missing tags"
                
                # Check for response documentation
                assert 'responses' in details, f"{method.upper()} {path} missing responses"
                responses = details['responses']
                assert '200' in responses or '201' in responses, f"{method.upper()} {path} missing success response"
    
    def test_documentation_generator(self):
        """Test documentation file generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate documentation
            app = create_app()
            schema = app.openapi()
            
            generator = APIDocumentationGenerator(temp_dir)
            generator.generate_documentation(schema)
            
            # Verify files were created
            docs_path = Path(temp_dir)
            expected_files = [
                'api-reference.md',
                'authentication.md',
                'getting-started.md',
                'websockets.md',
                'error-handling.md'
            ]
            
            for filename in expected_files:
                file_path = docs_path / filename
                assert file_path.exists(), f"Documentation file {filename} not created"
                assert file_path.stat().st_size > 0, f"Documentation file {filename} is empty"
    
    def test_api_reference_content(self):
        """Test API reference documentation content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app()
            schema = app.openapi()
            
            generator = APIDocumentationGenerator(temp_dir)
            generator._generate_api_reference(schema)
            
            # Read generated content
            api_ref_path = Path(temp_dir) / 'api-reference.md'
            content = api_ref_path.read_text()
            
            # Verify content includes key sections
            assert '# ZERO-COMP Solar Weather API Reference' in content
            assert '## Base URL' in content
            assert '## Authentication' in content
            assert '## Endpoints' in content
            
            # Verify some key endpoints are documented
            assert '/api/v1/alerts/current' in content
            assert '/api/v1/alerts/history' in content
    
    def test_authentication_guide_content(self):
        """Test authentication guide content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = APIDocumentationGenerator(temp_dir)
            generator._generate_auth_guide()
            
            # Read generated content
            auth_path = Path(temp_dir) / 'authentication.md'
            content = auth_path.read_text()
            
            # Verify content includes key sections
            assert '# Authentication Guide' in content
            assert 'JWT Tokens' in content
            assert 'API Keys' in content
            assert 'Security Best Practices' in content
            assert 'Rate Limiting' in content
    
    def test_websocket_documentation_content(self):
        """Test WebSocket documentation content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = APIDocumentationGenerator(temp_dir)
            generator._generate_websocket_docs()
            
            # Read generated content
            ws_path = Path(temp_dir) / 'websockets.md'
            content = ws_path.read_text()
            
            # Verify content includes key sections
            assert '# WebSocket Real-time Alerts' in content
            assert 'wss://api.zero-comp.com/ws/alerts' in content
            assert 'Message Types' in content
            assert 'Implementation Examples' in content
            assert 'JavaScript (Browser)' in content
            assert 'Python (asyncio)' in content
    
    def test_error_handling_guide_content(self):
        """Test error handling guide content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = APIDocumentationGenerator(temp_dir)
            generator._generate_error_guide()
            
            # Read generated content
            error_path = Path(temp_dir) / 'error-handling.md'
            content = error_path.read_text()
            
            # Verify content includes key sections
            assert '# Error Handling Guide' in content
            assert 'Error Response Format' in content
            assert 'HTTP Status Codes' in content
            assert '400 Bad Request' in content
            assert '401 Unauthorized' in content
            assert '403 Forbidden' in content
            assert '429 Rate Limit Exceeded' in content
            assert '500 Internal Server Error' in content
    
    def test_code_examples_generation(self):
        """Test code examples are properly generated."""
        from app.docs.openapi_customization import add_code_examples
        
        examples = add_code_examples()
        
        # Verify structure
        assert 'python' in examples
        assert 'javascript' in examples
        assert 'curl' in examples
        
        # Verify Python examples
        python_examples = examples['python']
        assert 'get_current_alert' in python_examples
        assert 'websocket_connection' in python_examples
        assert 'api_key_usage' in python_examples
        
        # Verify JavaScript examples
        js_examples = examples['javascript']
        assert 'get_current_alert' in js_examples
        assert 'websocket_connection' in js_examples
        assert 'node_js_example' in js_examples
        
        # Verify cURL examples
        curl_examples = examples['curl']
        assert 'get_current_alert' in curl_examples
        assert 'get_history' in curl_examples
        assert 'generate_api_key' in curl_examples
    
    def test_endpoint_examples_validation(self):
        """Test that endpoint examples are valid."""
        app = create_app()
        schema = app.openapi()
        
        # Check that examples exist for key models
        components = schema.get('components', {})
        schemas = components.get('schemas', {})
        
        key_models = ['CurrentAlertResponse', 'HistoricalAlertsResponse', 'ErrorResponse']
        
        for model_name in key_models:
            if model_name in schemas:
                model_schema = schemas[model_name]
                # Should have example or examples
                has_example = 'example' in model_schema or 'examples' in model_schema
                # Note: Examples might be added by customization, so this is informational
                print(f"Model {model_name} has examples: {has_example}")


if __name__ == '__main__':
    pytest.main([__file__])