#!/usr/bin/env python3
"""
Comprehensive test runner script for the Solar Weather API project.
Provides easy commands to run different types of tests with proper configuration.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description or cmd}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        return False
    else:
        print(f"✅ Command succeeded: {description or cmd}")
        return True


def setup_test_environment():
    """Set up test environment variables."""
    env_vars = {
        "ENVIRONMENT": "test",
        "SUPABASE_URL": "http://localhost:54321",
        "SUPABASE_ANON_KEY": "test_key",
        "SUPABASE_SERVICE_ROLE_KEY": "test_service_key",
        "RAZORPAY_KEY_ID": "test_razorpay_key",
        "RAZORPAY_KEY_SECRET": "test_razorpay_secret",
        "HUGGINGFACE_API_TOKEN": "test_hf_token",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
        "REDIS_URL": "redis://localhost:6379"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Test environment variables set")


def run_unit_tests(coverage=True, verbose=True):
    """Run unit tests."""
    cmd_parts = ["pytest", "tests/unit/"]
    
    if verbose:
        cmd_parts.append("-v")
    
    if coverage:
        cmd_parts.extend([
            "--cov=app",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "--cov-fail-under=90"
        ])
    
    cmd_parts.extend(["-m", "unit"])
    
    return run_command(" ".join(cmd_parts), "Unit Tests")


def run_integration_tests(verbose=True):
    """Run integration tests."""
    cmd_parts = ["pytest", "tests/integration/"]
    
    if verbose:
        cmd_parts.append("-v")
    
    cmd_parts.extend(["-m", "integration"])
    
    return run_command(" ".join(cmd_parts), "Integration Tests")


def run_e2e_tests(verbose=True):
    """Run end-to-end tests."""
    cmd_parts = ["pytest", "tests/e2e/"]
    
    if verbose:
        cmd_parts.append("-v")
    
    cmd_parts.extend(["-m", "e2e"])
    
    return run_command(" ".join(cmd_parts), "End-to-End Tests")


def run_performance_tests(verbose=True):
    """Run performance tests."""
    cmd_parts = ["pytest", "tests/performance/"]
    
    if verbose:
        cmd_parts.append("-v")
    
    cmd_parts.extend(["-m", "performance", "--tb=short"])
    
    return run_command(" ".join(cmd_parts), "Performance Tests")


def run_security_tests():
    """Run security tests."""
    success = True
    
    # Run Bandit security scan
    if not run_command("bandit -r app/ -f txt", "Bandit Security Scan"):
        success = False
    
    # Run Safety vulnerability check
    if not run_command("safety check", "Safety Vulnerability Check"):
        success = False
    
    return success


def run_code_quality_checks():
    """Run code quality checks."""
    success = True
    
    # Check code formatting
    if not run_command("black --check app/ tests/", "Black Code Formatting Check"):
        success = False
    
    # Check import sorting
    if not run_command("isort --check-only app/ tests/", "Import Sorting Check"):
        success = False
    
    # Run linting
    if not run_command("flake8 app/ tests/ --max-line-length=100 --extend-ignore=E203,W503", "Flake8 Linting"):
        success = False
    
    # Run type checking
    if not run_command("mypy app/ --ignore-missing-imports --no-strict-optional", "MyPy Type Checking"):
        success = False
    
    return success


def run_all_tests(skip_slow=False):
    """Run all tests in sequence."""
    setup_test_environment()
    
    results = []
    
    # Unit tests (always run)
    results.append(("Unit Tests", run_unit_tests()))
    
    # Integration tests
    results.append(("Integration Tests", run_integration_tests()))
    
    # E2E tests
    if not skip_slow:
        results.append(("E2E Tests", run_e2e_tests()))
    
    # Performance tests (only if not skipping slow tests)
    if not skip_slow:
        results.append(("Performance Tests", run_performance_tests()))
    
    # Security tests
    results.append(("Security Tests", run_security_tests()))
    
    # Code quality
    results.append(("Code Quality", run_code_quality_checks()))
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if not passed:
            all_passed = False
    
    print(f"{'='*60}")
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("💥 SOME TESTS FAILED!")
        return 1


def install_dependencies():
    """Install test dependencies."""
    return run_command("pip install -r requirements.txt", "Installing Dependencies")


def clean_test_artifacts():
    """Clean up test artifacts."""
    artifacts = [
        "htmlcov/",
        "coverage.xml",
        "coverage.json",
        "pytest-results.xml",
        ".coverage",
        ".pytest_cache/",
        "__pycache__/",
        "*.pyc"
    ]
    
    for artifact in artifacts:
        if os.path.exists(artifact):
            if os.path.isdir(artifact):
                run_command(f"rm -rf {artifact}", f"Removing {artifact}")
            else:
                run_command(f"rm -f {artifact}", f"Removing {artifact}")
    
    print("✅ Test artifacts cleaned")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Solar Weather API Test Runner")
    parser.add_argument("--type", choices=["unit", "integration", "e2e", "performance", "security", "quality", "all"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--quiet", action="store_true", help="Run tests quietly")
    parser.add_argument("--skip-slow", action="store_true", help="Skip slow tests (e2e, performance)")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies before running tests")
    parser.add_argument("--clean", action="store_true", help="Clean test artifacts before running")
    parser.add_argument("--clean-only", action="store_true", help="Only clean test artifacts")
    
    args = parser.parse_args()
    
    if args.clean_only:
        clean_test_artifacts()
        return 0
    
    if args.install_deps:
        if not install_dependencies():
            return 1
    
    if args.clean:
        clean_test_artifacts()
    
    setup_test_environment()
    
    verbose = not args.quiet
    coverage = not args.no_coverage
    
    if args.type == "unit":
        success = run_unit_tests(coverage=coverage, verbose=verbose)
    elif args.type == "integration":
        success = run_integration_tests(verbose=verbose)
    elif args.type == "e2e":
        success = run_e2e_tests(verbose=verbose)
    elif args.type == "performance":
        success = run_performance_tests(verbose=verbose)
    elif args.type == "security":
        success = run_security_tests()
    elif args.type == "quality":
        success = run_code_quality_checks()
    elif args.type == "all":
        return run_all_tests(skip_slow=args.skip_slow)
    else:
        print(f"Unknown test type: {args.type}")
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())