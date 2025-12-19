"""
Databricks Health Monitor - Test Suite
=======================================

Test categories:
- unit: Tests that don't require Spark (mocked)
- integration: Tests that require a local Spark session
- ml: ML model training and inference tests
- tvf: Table-Valued Function tests
- feature: Feature engineering tests

Run tests:
    pytest tests/ -v                    # All tests
    pytest tests/ -v -m unit            # Unit tests only
    pytest tests/ -v -m integration     # Integration tests only
    pytest tests/ -v -m ml              # ML tests only
    pytest tests/ -v --cov=src          # With coverage
"""
