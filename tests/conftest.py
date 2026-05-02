"""Fixtures and constants for Prowlpy tests."""

import pytest
from pyreqwest.pytest_plugin import ClientMocker

from prowlpy import Prowl
from tests.constants import VALID_API_KEY


@pytest.fixture
def prowl() -> Prowl:
    """Create a Prowl instance with a valid API key."""
    return Prowl(apikey=VALID_API_KEY)


@pytest.fixture
def mock_api(client_mocker: ClientMocker) -> ClientMocker:
    """Set up mock API responses."""
    return client_mocker.strict(enabled=True)
