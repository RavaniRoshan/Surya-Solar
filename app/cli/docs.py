"""CLI commands for generating API documentation."""

import asyncio
import json
from pathlib import Path
import click

from app.main import create_app
from app.docs.generator import APIDocumentationGenerator


@click.group()
def docs():
    """API documentation generation commands."""
    pass


@docs.command()
@click.option('--output-dir', '-o', default='docs/api', help='Output directory for documentation')
@click.option('--format', '-f', type=click.Choice(['markdown', 'html', 'json']), default='markdown', help='Output format')
def generate(output_dir: str, format: str):
    """Generate comprehensive API documentation."""
    
    click.echo("🚀 Generating ZERO-COMP API documentation...")
    
    # Create FastAPI app to get OpenAPI schema
    app = create_app()
    openapi_schema = app.openapi()
    
    if format == 'json':
        # Save OpenAPI schema as JSON
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        with open(output_path / 'openapi.json', 'w') as f:
            json.dump(openapi_schema, f, indent=2)
        
        click.echo(f"✅ OpenAPI schema saved to {output_path / 'openapi.json'}")
        
    elif format == 'markdown':
        # Generate markdown documentation
        generator = APIDocumentationGenerator(output_dir)
        generator.generate_documentation(openapi_schema)
        
        click.echo(f"✅ Markdown documentation generated in {output_dir}")
        
    elif format == 'html':
        # Generate HTML documentation (future feature)
        click.echo("❌ HTML format not yet implemented")
        return
    
    click.echo("📚 Documentation generation complete!")


@docs.command()
@click.option('--port', '-p', default=8080, help='Port to serve documentation on')
def serve(port: int):
    """Serve documentation locally for development."""
    
    import http.server
    import socketserver
    import os
    
    docs_dir = Path('docs/api')
    if not docs_dir.exists():
        click.echo("❌ Documentation not found. Run 'generate' command first.")
        return
    
    os.chdir(docs_dir)
    
    with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
        click.echo(f"📖 Serving documentation at http://localhost:{port}")
        click.echo("Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\n👋 Documentation server stopped")


@docs.command()
def validate():
    """Validate OpenAPI schema and documentation."""
    
    click.echo("🔍 Validating API documentation...")
    
    try:
        # Create app and get schema
        app = create_app()
        openapi_schema = app.openapi()
        
        # Basic validation
        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in openapi_schema:
                click.echo(f"❌ Missing required field: {field}")
                return
        
        # Count endpoints
        paths = openapi_schema.get('paths', {})
        endpoint_count = sum(len(methods) for methods in paths.values())
        
        click.echo(f"✅ OpenAPI schema is valid")
        click.echo(f"📊 Found {len(paths)} paths with {endpoint_count} endpoints")
        
        # Check for documentation completeness
        missing_descriptions = []
        for path, methods in paths.items():
            for method, details in methods.items():
                if 'description' not in details or not details['description'].strip():
                    missing_descriptions.append(f"{method.upper()} {path}")
        
        if missing_descriptions:
            click.echo(f"⚠️  {len(missing_descriptions)} endpoints missing descriptions:")
            for endpoint in missing_descriptions[:5]:  # Show first 5
                click.echo(f"   - {endpoint}")
            if len(missing_descriptions) > 5:
                click.echo(f"   ... and {len(missing_descriptions) - 5} more")
        else:
            click.echo("✅ All endpoints have descriptions")
        
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")


if __name__ == '__main__':
    docs()