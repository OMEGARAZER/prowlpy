"""Tests for the Prowlpy library."""

import pytest
import respx
from httpx import Response, TransportError

from prowlpy import APIError, MissingKeyError, Prowl
from tests.constants import VALID_API_KEY, VALID_PROVIDER_KEY, VALID_TOKEN, SUCCESS_RESPONSE, TOKEN_RESPONSE, APIKEY_RESPONSE, INVALID_XML_RESPONSE


def test_init_with_valid_apikey(prowl) -> None:
    """Test initialization with valid API key."""
    prowl = Prowl(apikey=VALID_API_KEY)
    assert prowl.apikey == VALID_API_KEY
    assert prowl.providerkey is None


def test_init_with_multiple_apikeys() -> None:
    """Test initialization with multiple API keys."""
    prowl = Prowl(apikey=[VALID_API_KEY, VALID_API_KEY])
    assert prowl.apikey == f"{VALID_API_KEY},{VALID_API_KEY}"
    assert prowl.providerkey is None


def test_init_with_provider_key() -> None:
    """Test initialization with provider key."""
    prowl = Prowl(apikey=VALID_API_KEY, providerkey=VALID_PROVIDER_KEY)
    assert prowl.apikey == VALID_API_KEY
    assert prowl.providerkey == VALID_PROVIDER_KEY


def test_init_with_only_provider_key() -> None:
    """Test initialization with only provider key."""
    prowl = Prowl(providerkey=VALID_PROVIDER_KEY)
    assert prowl.apikey is None
    assert prowl.providerkey == VALID_PROVIDER_KEY


def test_init_without_apikey() -> None:
    """Test initialization without API key raises error."""
    with pytest.raises(MissingKeyError, match="API Key or Provider Key are required"):
        Prowl(apikey="")


def test_context_manager() -> None:
    """Test context manager protocol."""
    with Prowl(apikey=VALID_API_KEY) as prowl:
        assert isinstance(prowl, Prowl)
        assert prowl.apikey == VALID_API_KEY


def test_context_manager_with_error() -> None:
    """Test context manager handles exceptions properly."""
    with pytest.raises(ValueError, match="Test error"), Prowl(apikey=VALID_API_KEY) as prowl:  # noqa: PT012
        assert isinstance(prowl, Prowl)
        raise ValueError("Test error")


def test_post_notification_success(mock_api: respx.Router) -> None:
    """Test successful notification post."""
    mock_api.post("/add").mock(return_value=Response(200, text=SUCCESS_RESPONSE))

    prowl = Prowl(apikey=VALID_API_KEY)
    prowl.post(application="Test App", event="Test Event", description="Test Description")


def test_post_notification_without_apikey() -> None:
    """Test notification post without apikey."""
    prowl = Prowl(providerkey=VALID_PROVIDER_KEY)
    with pytest.raises(MissingKeyError, match="API Key is required"):
        prowl.post(application="Test App", event="Test Event", description="Test Description")


def test_post_notification_with_all_params(mock_api: respx.Router) -> None:
    """Test notification post with all parameters."""
    mock_api.post("/add").mock(return_value=Response(200, text=SUCCESS_RESPONSE))

    prowl = Prowl(apikey=VALID_API_KEY)
    prowl.post(
        application="Test App",
        event="Test Event",
        description="Test Description",
        priority=2,
        url="https://example.com",
        providerkey=VALID_PROVIDER_KEY,
    )


def test_post_notification_with_both_keys_init(mock_api: respx.Router) -> None:
    """Test notification post with all parameters."""
    mock_api.post("/add").mock(return_value=Response(200, text=SUCCESS_RESPONSE))

    prowl = Prowl(apikey=VALID_API_KEY, providerkey=VALID_PROVIDER_KEY)
    prowl.post(application="Test App", event="Test Event", description="Test Description")


def test_post_notification_invalid_priority(mock_api: respx.Router) -> None:
    """Test notification post with invalid priority."""
    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(ValueError, match="Priority must be between -2 and 2"):
        prowl.post(application="Test App", event="Test Event", description="Test Description", priority=3)


def test_post_notification_missing_required(mock_api: respx.Router) -> None:
    """Test notification post without required fields."""
    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(ValueError, match="Must provide event, description or both"):
        prowl.post(application="Test App")


def test_post_notification_api_error(mock_api: respx.Router) -> None:
    """Test notification post with API error."""
    mock_api.post("/add").mock(return_value=Response(400, text="Bad Request"))

    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(APIError, match="Bad Request"):
        prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )


def test_verify_key_success(mock_api: respx.Router) -> None:
    """Test successful key verification."""
    mock_api.get("/verify").mock(return_value=Response(200, text=SUCCESS_RESPONSE))

    prowl = Prowl(apikey=VALID_API_KEY)
    prowl.verify_key(providerkey=VALID_PROVIDER_KEY)


def test_verify_key_success_with_providerkey_init(mock_api: respx.Router) -> None:
    """Test successful key verification."""
    mock_api.get("/verify").mock(return_value=Response(200, text=SUCCESS_RESPONSE))

    prowl = Prowl(apikey=VALID_API_KEY, providerkey=VALID_PROVIDER_KEY)
    prowl.verify_key()


def test_verify_key_invalid(mock_api: respx.Router) -> None:
    """Test invalid key verification."""
    mock_api.get("/verify").mock(return_value=Response(401, text="Invalid API key"))

    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(APIError, match=f"Invalid API key: {VALID_API_KEY}"):
        prowl.verify_key()


def test_verify_key_without_key() -> None:
    """Test key verification without key."""
    prowl = Prowl(providerkey=VALID_PROVIDER_KEY)
    with pytest.raises(MissingKeyError, match="API Key is required"):
        prowl.verify_key()


def test_retrieve_token_success(mock_api: respx.Router) -> None:
    """Test successful token retrieval."""
    mock_api.get("/retrieve/token").mock(return_value=Response(200, text=TOKEN_RESPONSE))

    result = Prowl(apikey=VALID_API_KEY).retrieve_token(providerkey=VALID_PROVIDER_KEY)
    assert "token" in result
    assert result["token"] == VALID_TOKEN


def test_retrieve_token_success_providerkey_init(mock_api: respx.Router) -> None:
    """Test successful token retrieval."""
    mock_api.get("/retrieve/token").mock(return_value=Response(200, text=TOKEN_RESPONSE))

    result = Prowl(apikey=VALID_API_KEY, providerkey=VALID_PROVIDER_KEY).retrieve_token()
    assert "token" in result
    assert result["token"] == VALID_TOKEN


def test_retrieve_apikey_success(mock_api: respx.Router) -> None:
    """Test successful API key retrieval."""
    mock_api.get("/retrieve/apikey").mock(return_value=Response(200, text=APIKEY_RESPONSE))

    result = Prowl(apikey=VALID_API_KEY).retrieve_apikey(providerkey=VALID_PROVIDER_KEY, token=VALID_TOKEN)
    assert "apikey" in result
    assert result["apikey"] == VALID_API_KEY


def test_retrieve_apikey_success_providerkey_init(mock_api: respx.Router) -> None:
    """Test successful API key retrieval."""
    mock_api.get("/retrieve/apikey").mock(return_value=Response(200, text=APIKEY_RESPONSE))

    result = Prowl(apikey=VALID_API_KEY, providerkey=VALID_PROVIDER_KEY).retrieve_apikey(token=VALID_TOKEN)
    assert "apikey" in result
    assert result["apikey"] == VALID_API_KEY


def test_retrieve_token_missing_provider_key(mock_api: respx.Router) -> None:
    """Test token retrieval without provider key."""
    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(MissingKeyError, match="Provider key is required"):
        prowl.retrieve_token()


def test_retrieve_token_error(mock_api: respx.Router) -> None:
    """Test error in token retrieval."""
    mock_api.get("/retrieve/token").mock(return_value=Response(400, text="Bad Request"))

    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(APIError, match="Bad Request"):
        prowl.retrieve_token(providerkey=VALID_PROVIDER_KEY)


def test_retrieve_apikey_error(mock_api: respx.Router) -> None:
    """Test error in API key retrieval."""
    mock_api.get("/retrieve/apikey").mock(return_value=Response(400, text="Bad Request"))

    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(APIError, match="Bad Request"):
        prowl.retrieve_apikey(providerkey=VALID_PROVIDER_KEY, token=VALID_TOKEN)


def test_retrieve_apikey_missing_provider_key(mock_api: respx.Router) -> None:
    """Test API key retrieval without provider key."""
    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(MissingKeyError, match="Provider key is required"):
        prowl.retrieve_apikey(providerkey="", token=VALID_TOKEN)


def test_retrieve_apikey_missing_token(mock_api: respx.Router) -> None:
    """Test API key retrieval without token."""
    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(MissingKeyError, match="Token is required"):
        prowl.retrieve_apikey(providerkey=VALID_PROVIDER_KEY, token="")


def test_retrieve_token_invalid_xml(mock_api: respx.Router) -> None:
    """Test retrieve_token with invalid XML response."""
    mock_api.get("/retrieve/token").mock(return_value=Response(200, text=INVALID_XML_RESPONSE))

    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(KeyError):
        prowl.retrieve_token(providerkey=VALID_PROVIDER_KEY)


def test_retrieve_apikey_invalid_xml(mock_api: respx.Router) -> None:
    """Test retrieve_apikey with invalid XML response."""
    mock_api.get("/retrieve/apikey").mock(return_value=Response(200, text=INVALID_XML_RESPONSE))

    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(KeyError):
        prowl.retrieve_apikey(providerkey=VALID_PROVIDER_KEY, token=VALID_TOKEN)


def test_post_unknown_error(mock_api: respx.Router) -> None:
    """Test post with unknown error code."""
    mock_api.post("/add").mock(return_value=Response(418, text="I'm a teapot"))

    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(APIError, match="Unknown API error: Error code 418"):
        prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )


def test_post_rate_limit_error(mock_api: respx.Router) -> None:
    """Test post with rate limit error."""
    mock_api.post("/add").mock(return_value=Response(406, text="Rate limit exceeded"))

    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(APIError, match="Not accepted: Your IP address has exceeded the API limit"):
        prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )


def test_post_not_approved_error(mock_api: respx.Router) -> None:
    """Test post with not approved error."""
    mock_api.post("/add").mock(return_value=Response(409, text="Not approved"))

    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(APIError, match="Not approved: The user has yet to approve your retrieve request"):
        prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )


def test_post_server_error(mock_api: respx.Router) -> None:
    """Test post with server error."""
    mock_api.post("/add").mock(return_value=Response(500, text="Internal Server Error"))

    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(APIError, match="Internal server error"):
        prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )


def test_post_network_error(mock_api: respx.Router) -> None:
    """Test post with network error."""
    mock_api.post("/add").mock(side_effect=TransportError("Connection error"))

    prowl = Prowl(apikey=VALID_API_KEY)
    with pytest.raises(APIError, match="API connection error: Connection error"):
        prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )
