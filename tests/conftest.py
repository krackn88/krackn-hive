"""Pytest fixtures and configuration."""

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"
