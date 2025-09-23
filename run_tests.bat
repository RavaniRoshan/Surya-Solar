@echo off
REM Comprehensive test runner for Windows
REM Usage: run_tests.bat [test_type] [options]

setlocal enabledelayedexpansion

REM Set test environment variables
set ENVIRONMENT=test
set SUPABASE_URL=http://localhost:54321
set SUPABASE_ANON_KEY=test_key
set SUPABASE_SERVICE_ROLE_KEY=test_service_key
set RAZORPAY_KEY_ID=test_razorpay_key
set RAZORPAY_KEY_SECRET=test_razorpay_secret
set HUGGINGFACE_API_TOKEN=test_hf_token
set DATABASE_URL=postgresql://test:test@localhost:5432/test_db
set REDIS_URL=redis://localhost:6379

echo ============================================================
echo Solar Weather API Test Runner
echo ============================================================

REM Parse command line arguments
set TEST_TYPE=%1
if "%TEST_TYPE%"=="" set TEST_TYPE=all

if "%TEST_TYPE%"=="unit" goto run_unit
if "%TEST_TYPE%"=="integration" goto run_integration
if "%TEST_TYPE%"=="e2e" goto run_e2e
if "%TEST_TYPE%"=="performance" goto run_performance
if "%TEST_TYPE%"=="security" goto run_security
if "%TEST_TYPE%"=="quality" goto run_quality
if "%TEST_TYPE%"=="all" goto run_all
if "%TEST_TYPE%"=="clean" goto clean_artifacts

echo Unknown test type: %TEST_TYPE%
echo Available types: unit, integration, e2e, performance, security, quality, all, clean
goto end

:run_unit
echo Running Unit Tests...
pytest tests/unit/ -v --cov=app --cov-report=html:htmlcov --cov-report=term-missing --cov-report=xml --cov-fail-under=90 -m unit
goto end

:run_integration
echo Running Integration Tests...
pytest tests/integration/ -v -m integration
goto end

:run_e2e
echo Running End-to-End Tests...
pytest tests/e2e/ -v -m e2e
goto end

:run_performance
echo Running Performance Tests...
pytest tests/performance/ -v -m performance --tb=short
goto end

:run_security
echo Running Security Tests...
echo Running Bandit security scan...
bandit -r app/ -f txt
echo Running Safety vulnerability check...
safety check
goto end

:run_quality
echo Running Code Quality Checks...
echo Checking code formatting...
black --check app/ tests/
echo Checking import sorting...
isort --check-only app/ tests/
echo Running linting...
flake8 app/ tests/ --max-line-length=100 --extend-ignore=E203,W503
echo Running type checking...
mypy app/ --ignore-missing-imports --no-strict-optional
goto end

:run_all
echo Running All Tests...
echo.
echo [1/6] Unit Tests
pytest tests/unit/ -v --cov=app --cov-report=html:htmlcov --cov-report=term-missing --cov-report=xml --cov-fail-under=90 -m unit
if errorlevel 1 set FAILED=1

echo.
echo [2/6] Integration Tests
pytest tests/integration/ -v -m integration
if errorlevel 1 set FAILED=1

echo.
echo [3/6] End-to-End Tests
pytest tests/e2e/ -v -m e2e
if errorlevel 1 set FAILED=1

echo.
echo [4/6] Performance Tests
pytest tests/performance/ -v -m performance --tb=short
if errorlevel 1 set FAILED=1

echo.
echo [5/6] Security Tests
bandit -r app/ -f txt
if errorlevel 1 set FAILED=1
safety check
if errorlevel 1 set FAILED=1

echo.
echo [6/6] Code Quality
black --check app/ tests/
if errorlevel 1 set FAILED=1
isort --check-only app/ tests/
if errorlevel 1 set FAILED=1
flake8 app/ tests/ --max-line-length=100 --extend-ignore=E203,W503
if errorlevel 1 set FAILED=1
mypy app/ --ignore-missing-imports --no-strict-optional
if errorlevel 1 set FAILED=1

echo.
echo ============================================================
echo TEST SUMMARY
echo ============================================================
if defined FAILED (
    echo Some tests failed!
    exit /b 1
) else (
    echo All tests passed!
    exit /b 0
)

:clean_artifacts
echo Cleaning test artifacts...
if exist htmlcov rmdir /s /q htmlcov
if exist coverage.xml del coverage.xml
if exist coverage.json del coverage.json
if exist pytest-results.xml del pytest-results.xml
if exist .coverage del .coverage
if exist .pytest_cache rmdir /s /q .pytest_cache
for /r %%i in (__pycache__) do if exist "%%i" rmdir /s /q "%%i"
for /r %%i in (*.pyc) do if exist "%%i" del "%%i"
echo Test artifacts cleaned!
goto end

:end
echo.
echo Test execution completed.