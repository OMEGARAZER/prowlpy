"""Fixtures and constants for Prowlpy tests."""
import pytest
import respx

from prowlpy import Prowl
from tests.constants import VALID_API_KEY

@pytest.fixture
def prowl():
    """Create a Prowl instance with a valid API key."""
    return Prowl(apikey=VALID_API_KEY)


@pytest.fixture
def mock_api():
    """Set up mock API responses."""
    with respx.mock(base_url="https://api.prowlapp.com/publicapi", assert_all_mocked=True) as respx_mock:
        yield respx_mock