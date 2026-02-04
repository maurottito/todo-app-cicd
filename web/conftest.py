"""pytest configuration and fixtures"""
import pytest


def pytest_configure(config):
    """Register custom pytest markers"""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test (requires real database)"
    )
