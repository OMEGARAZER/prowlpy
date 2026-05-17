"""Tests for the Prowlpy CLI module."""

import importlib
import sys

import pytest
from loguru import logger
from pyreqwest.exceptions import RequestTimeoutError
from pyreqwest.pytest_plugin import ClientMocker, Mock
from pyreqwest.request import Request
from typer.testing import CliRunner

from prowlpy._cli import app  # noqa: PLC2701
from prowlpy.prowlpy import __version__


@pytest.fixture(autouse=True)
def mock_logger():  # noqa: ANN201
    """Mock Loguru logger."""
    logger.remove()
    logger.add(sink=lambda msg: print(msg, end=""))  # noqa: T201
    yield
    logger.remove()


@pytest.fixture
def mock_prowl_api(client_mocker: ClientMocker) -> Mock:
    """Set up mock Prowl API call."""
    return (
        client_mocker
        .strict(enabled=True)
        .post(path="/publicapi/add")
        .with_status(status=200)
        .with_body_text(
            body='<?xml version="1.0" encoding="UTF-8"?><prowl><success code="200" remaining="999" '
            'resetdate="1735714800"/></prowl>',
        )
    )


@pytest.fixture
def mock_pypi_api(client_mocker: ClientMocker) -> Mock:
    """Set up mock Pypi API call."""
    return (
        client_mocker
        .strict(enabled=True)
        .get(path="/pypi/prowlpy/json")
        .with_status(status=200)
        .with_body_json(json_body={"info": {"version": __version__}})
    )


def test_help_output() -> None:
    """Test call to --help."""
    result = CliRunner().invoke(app=app, args=["--help"])
    assert result.exit_code == 0
    assert "Prowlpy" in result.output
    assert "--apikey" in result.output
    assert "--application" in result.output


def test_version_check(mock_pypi_api: ClientMocker) -> None:
    """Test call to --version."""
    result = CliRunner().invoke(app=app, args=["--version"])
    assert result.exit_code == 0
    assert "You are currently using v" in result.output
    assert f"v{__version__}" in result.output
    mock_pypi_api.assert_called(count=1)  # pyright: ignore[reportAttributeAccessIssue] # ty:ignore[unresolved-attribute]


def test_no_arguments() -> None:
    """Test call with no arguments provided."""
    original_argv = sys.argv
    try:
        sys.argv = ["prowlpy.py"]
        result = CliRunner().invoke(app=app)
        assert result.exit_code == 1
        assert "Prowlpy" in result.output
    finally:
        sys.argv = original_argv


def test_successful_message_send(mock_prowl_api: ClientMocker) -> None:
    """Test for successful message."""
    result = CliRunner().invoke(
        app=app,
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
    last_request = dict(mock_prowl_api.get_requests()[-1].url.query_pairs)
    assert last_request["apikey"] == "test_key"
    assert last_request["application"] == "Test App"


def test_missing_required_params() -> None:
    """Test with missing Application name."""
    result = CliRunner().invoke(app=app, args=["--apikey", "test_key"])
    assert result.exit_code == 1
    assert "Must provide application" in result.output


def test_invalid_priority(mock_prowl_api: ClientMocker) -> None:
    """Test with invalid/clamped priority."""
    result = CliRunner().invoke(
        app=app,
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
    last_request = dict(mock_prowl_api.get_requests()[-1].url.query_pairs)
    assert last_request["priority"] == "2"
    assert "Message sent" in result.output


def test_pypi_timeout(client_mocker: ClientMocker) -> None:
    """Test timeout in version check."""

    def raise_timeout_error(_request: Request) -> None:
        raise RequestTimeoutError("Connection error", {"causes": None})

    client_mocker.get(path="/pypi/prowlpy/json").match_request_with_response(handler=raise_timeout_error)
    result = CliRunner().invoke(app=app, args=["--version"])
    assert result.exit_code == 0
    assert "Timeout reached fetching current version" in result.output


def test_pypi_server_error(client_mocker: ClientMocker) -> None:
    """Test status error in version check."""
    client_mocker.get(path="/pypi/prowlpy/json").with_status(status=500).with_body_text(body="Internal Server Error")
    result = CliRunner().invoke(app=app, args=["--version"])
    assert result.exit_code == 0
    assert "Unable to fetch latest version" in result.output


def test_pypi_invalid_json(client_mocker: ClientMocker) -> None:
    """Test invalid JSON returned by Pypi."""
    client_mocker.get(path="/pypi/prowlpy/json").with_status(status=200).with_body_text(body="No JSON here")
    result = CliRunner().invoke(app=app, args=["--version"])
    assert result.exit_code == 0
    assert "Unable to fetch latest version" in result.output


def test_multiple_apikeys(mock_prowl_api: ClientMocker) -> None:
    """Test with multiple API keys set."""
    result = CliRunner().invoke(
        app=app,
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
    last_request = dict(mock_prowl_api.get_requests()[-1].url.query_pairs)
    assert last_request["apikey"] == "key1,key2"


def test_missing_cli_components(monkeypatch, capsys) -> None:  # noqa: ANN001
    """Test with missing CLI components."""
    monkeypatch.setitem(sys.modules, "click", None)
    monkeypatch.setitem(sys.modules, "loguru", None)
    monkeypatch.delitem(sys.modules, "prowlpy._cli", raising=False)
    with pytest.raises(expected_exception=SystemExit) as exc_info:
        importlib.import_module(name="prowlpy._cli")
    assert exc_info.value.code == 1
    assert "install prowlpy[cli]" in capsys.readouterr().out
