def pytest_configure(config):
    """Register custom pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires real database)"
    )
