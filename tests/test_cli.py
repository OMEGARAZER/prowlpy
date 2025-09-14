"""Tests for the Prowlpy CLI module."""

import sys

import pytest
import respx
from click.testing import CliRunner
from httpx import Response
from loguru import logger

from prowlpy._cli import __version__, main  # noqa: PLC2701


@pytest.fixture(autouse=True)
def mock_logger():
    """Mock Loguru logger."""
    logger.remove()
    logger.add(lambda msg: print(msg, end=""))  # noqa: T201
    yield
    logger.remove()


@pytest.fixture
def mock_prowl_api():
    """Set up mock Prowl API call."""
    with respx.mock(assert_all_mocked=True) as respx_mock:
        respx_mock.post("https://api.prowlapp.com/publicapi/add").mock(
            return_value=Response(
                status_code=200,
                text='<?xml version="1.0" encoding="UTF-8"?><prowl><success code="200" remaining="999" '
                'resetdate="1735714800"/></prowl>',
            ),
        )
        yield respx_mock


@pytest.fixture
def mock_pypi_api():
    """Set up mock Pypi API call."""
    with respx.mock(assert_all_mocked=True) as respx_mock:
        respx_mock.get("https://pypi.org/pypi/prowlpy/json").mock(
            return_value=Response(
                status_code=200,
                json={"info": {"version": __version__}},
            ),
        )
        yield respx_mock


def test_help_output():
    """Test call to --help."""
    result = CliRunner().invoke(cli=main, args=["--help"])
    assert result.exit_code == 0
    assert "Prowlpy" in result.output
    assert "--apikey" in result.output
    assert "--application" in result.output


def test_version_check(mock_pypi_api):  # noqa: ANN001
    """Test call to --version."""
    result = CliRunner().invoke(cli=main, args=["--version"])
    assert result.exit_code == 0
    assert "You are currently using v" in result.output
    assert mock_pypi_api.calls.last.response.json()["info"]["version"] == __version__


def test_no_arguments():
    """Test call with no arguments provided."""
    original_argv = sys.argv
    try:
        sys.argv = ["prowlpy.py"]
        result = CliRunner().invoke(cli=main)
        assert result.exit_code == 1
        assert "Prowlpy" in result.output
    finally:
        sys.argv = original_argv


def test_successful_message_send(mock_prowl_api):  # noqa: ANN001
    """Test for successful message."""
    result = CliRunner().invoke(
        cli=main,
        args=[
            "--apikey",
            "test_key",
            "--application",
            "Test App",
            "--event",
            "Test Event",
            "--description",
            "Test Description",
        ],
    )
    assert result.exit_code == 0
    assert "Message sent, rate limit remaining 999" in result.output
    assert mock_prowl_api.calls.last.request.url.params["apikey"] == "test_key"
    assert mock_prowl_api.calls.last.request.url.params["application"] == "Test App"


def test_missing_required_params():
    """Test with missing Application name."""
    result = CliRunner().invoke(cli=main, args=["--apikey", "test_key"])
    assert result.exit_code == 1
    assert "Must provide application" in result.output


def test_invalid_priority(mock_prowl_api):  # noqa: ANN001
    """Test with invalid/clamped priority."""
    result = CliRunner().invoke(
        cli=main,
        args=[
            "--apikey",
            "test_key",
            "--application",
            "Test App",
            "--event",
            "Test Event",
            "--priority",
            "3",
        ],
    )
    assert result.exit_code == 0
    assert mock_prowl_api.calls.last.request.url.params["priority"] == "2"
    assert "Message sent" in result.output


def test_pypi_timeout():
    """Test timeout in version check."""
    with respx.mock(assert_all_mocked=True) as respx_mock:
        respx_mock.get("https://pypi.org/pypi/prowlpy/json").mock(side_effect=TimeoutError)
        result = CliRunner().invoke(cli=main, args=["--version"])
        assert result.exit_code == 0
        assert "Timeout reached fetching current version" in result.output


def test_multiple_apikeys(mock_prowl_api):  # noqa: ANN001
    """Test with multiple API keys set."""
    result = CliRunner().invoke(
        cli=main,
        args=[
            "--apikey",
            "key1",
            "--apikey",
            "key2",
            "--application",
            "Test App",
            "--event",
            "Test Event",
        ],
    )
    assert result.exit_code == 0
    assert "Message sent" in result.output
    assert mock_prowl_api.calls.last.request.url.params["apikey"] == "key1,key2"
