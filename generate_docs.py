#!/usr/bin/env python3
"""Simple script to generate API documentation without full app initialization."""

import os
import sys
import json
from pathlib import Path

# Set minimal environment variables
os.environ.setdefault('SUPABASE_URL', 'https://dummy.supabase.co')
os.environ.setdefault('SUPABASE_ANON_KEY', 'dummy_key')
os.environ.setdefault('SUPABASE_SERVICE_KEY', 'dummy_key')
os.environ.setdefault('DATABASE_URL', 'postgresql://dummy:dummy@localhost:5432/dummy')

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import create_app
    from app.docs.generator import APIDocumentationGenerator
    
    print("🚀 Generating ZERO-COMP API documentation...")
    
    # Create FastAPI app to get OpenAPI schema
    app = create_app()
    openapi_schema = app.openapi()
    
    # Generate markdown documentation
    output_dir = 'docs/api'
    generator = APIDocumentationGenerator(output_dir)
    generator.generate_documentation(openapi_schema)
    
    # Also save OpenAPI schema as JSON
    output_path = Path(output_dir)
    with open(output_path / 'openapi.json', 'w') as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"✅ OpenAPI schema saved to {output_path / 'openapi.json'}")
    print("📚 Documentation generation complete!")
    
except Exception as e:
    print(f"❌ Error generating documentation: {e}")
    import traceback
    traceback.print_exc()