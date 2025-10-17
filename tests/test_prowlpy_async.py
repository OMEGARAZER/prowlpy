"""Tests for the Async Prowlpy library."""

import pytest
import respx
from httpx import AsyncClient, Response, TransportError

from prowlpy import APIError, AsyncProwl, MissingKeyError
from tests.constants import (
    APIKEY_RESPONSE,
    INVALID_XML_RESPONSE,
    SUCCESS_RESPONSE,
    TOKEN_RESPONSE,
    VALID_API_KEY,
    VALID_PROVIDER_KEY,
    VALID_TOKEN,
)


def test_async_init_with_valid_apikey() -> None:
    """Test initialization with valid API key."""
    prowl = AsyncProwl(apikey=VALID_API_KEY)
    assert prowl.apikey == VALID_API_KEY
    assert prowl.providerkey is None


def test_async_init_with_multiple_apikeys() -> None:
    """Test initialization with multiple API keys."""
    prowl = AsyncProwl(apikey=[VALID_API_KEY, VALID_API_KEY])
    assert prowl.apikey == f"{VALID_API_KEY},{VALID_API_KEY}"
    assert prowl.providerkey is None


def test_async_init_with_provider_key() -> None:
    """Test initialization with provider key."""
    prowl = AsyncProwl(apikey=VALID_API_KEY, providerkey=VALID_PROVIDER_KEY)
    assert prowl.apikey == VALID_API_KEY
    assert prowl.providerkey == VALID_PROVIDER_KEY


def test_async_init_with_only_provider_key() -> None:
    """Test initialization with only provider key."""
    prowl = AsyncProwl(providerkey=VALID_PROVIDER_KEY)
    assert prowl.apikey is None
    assert prowl.providerkey == VALID_PROVIDER_KEY


def test_async_init_without_apikey() -> None:
    """Test initialization without API key raises error."""
    with pytest.raises(expected_exception=MissingKeyError, match="API Key or Provider Key are required"):
        AsyncProwl(apikey="")


@pytest.mark.asyncio
async def test_async_context_manager() -> None:
    """Test context manager protocol."""
    async with AsyncProwl(apikey=VALID_API_KEY) as prowl:
        assert isinstance(prowl, AsyncProwl)
        assert prowl.apikey == VALID_API_KEY


@pytest.mark.asyncio
async def test_async_context_manager_with_error() -> None:
    """Test context manager handles exceptions properly."""
    with pytest.raises(expected_exception=ValueError, match="Test error"):  # noqa: PT012
        async with AsyncProwl(apikey=VALID_API_KEY) as prowl:
            assert isinstance(prowl, AsyncProwl)
            raise ValueError("Test error")


@pytest.mark.asyncio
async def test_async_post_notification_success(mock_api: respx.Router) -> None:
    """Test successful notification post."""
    mock_api.post(url="/add").mock(return_value=Response(status_code=200, text=SUCCESS_RESPONSE))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    await prowl.post(application="Test App", event="Test Event", description="Test Description")


@pytest.mark.asyncio
async def test_async_send_notification_success(mock_api: respx.Router) -> None:
    """Test successful notification send."""
    mock_api.post(url="/add").mock(return_value=Response(status_code=200, text=SUCCESS_RESPONSE))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    await prowl.send(application="Test App", event="Test Event", description="Test Description")


@pytest.mark.asyncio
async def test_async_add_notification_success(mock_api: respx.Router) -> None:
    """Test successful notification add."""
    mock_api.post(url="/add").mock(return_value=Response(status_code=200, text=SUCCESS_RESPONSE))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    await prowl.add(application="Test App", event="Test Event", description="Test Description")


@pytest.mark.asyncio
async def test_async_post_notification_without_apikey() -> None:
    """Test notification post without apikey."""
    prowl = AsyncProwl(providerkey=VALID_PROVIDER_KEY)
    with pytest.raises(expected_exception=MissingKeyError, match="API Key is required"):
        await prowl.post(application="Test App", event="Test Event", description="Test Description")


@pytest.mark.asyncio
async def test_async_post_notification_with_all_params(mock_api: respx.Router) -> None:
    """Test notification post with all parameters."""
    mock_api.post(url="/add").mock(return_value=Response(status_code=200, text=SUCCESS_RESPONSE))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    await prowl.post(
        application="Test App",
        event="Test Event",
        description="Test Description",
        priority=2,
        url="https://example.com",
        providerkey=VALID_PROVIDER_KEY,
    )


@pytest.mark.asyncio
async def test_async_post_notification_with_both_keys_init(mock_api: respx.Router) -> None:
    """Test notification post with all parameters."""
    mock_api.post(url="/add").mock(return_value=Response(status_code=200, text=SUCCESS_RESPONSE))

    prowl = AsyncProwl(apikey=VALID_API_KEY, providerkey=VALID_PROVIDER_KEY)
    await prowl.post(application="Test App", event="Test Event", description="Test Description")


@pytest.mark.asyncio
async def test_async_post_notification_invalid_priority(mock_api: respx.Router) -> None:
    """Test notification post with invalid priority."""
    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=ValueError, match="Priority must be between -2 and 2"):
        await prowl.post(application="Test App", event="Test Event", description="Test Description", priority=3)


@pytest.mark.asyncio
async def test_async_post_notification_missing_required(mock_api: respx.Router) -> None:
    """Test notification post without required fields."""
    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=ValueError, match="Must provide event, description or both"):
        await prowl.post(application="Test App")


@pytest.mark.asyncio
async def test_async_post_notification_api_error(mock_api: respx.Router) -> None:
    """Test notification post with API error."""
    mock_api.post(url="/add").mock(return_value=Response(status_code=400, text="Bad Request"))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=APIError, match="Bad Request"):
        await prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )


@pytest.mark.asyncio
async def test_async_verify_key_success(mock_api: respx.Router) -> None:
    """Test successful key verification."""
    mock_api.get(url="/verify").mock(return_value=Response(status_code=200, text=SUCCESS_RESPONSE))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    await prowl.verify_key(providerkey=VALID_PROVIDER_KEY)


@pytest.mark.asyncio
async def test_async_verify_key_success_with_providerkey_init(mock_api: respx.Router) -> None:
    """Test successful key verification."""
    mock_api.get(url="/verify").mock(return_value=Response(status_code=200, text=SUCCESS_RESPONSE))

    prowl = AsyncProwl(apikey=VALID_API_KEY, providerkey=VALID_PROVIDER_KEY)
    await prowl.verify_key()


@pytest.mark.asyncio
async def test_async_verify_key_invalid(mock_api: respx.Router) -> None:
    """Test invalid key verification."""
    mock_api.get(url="/verify").mock(return_value=Response(status_code=401, text="Invalid API key"))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=APIError, match=f"Invalid API key: {VALID_API_KEY}"):
        await prowl.verify_key()


@pytest.mark.asyncio
async def test_async_verify_key_without_key() -> None:
    """Test key verification without key."""
    prowl = AsyncProwl(providerkey=VALID_PROVIDER_KEY)
    with pytest.raises(expected_exception=MissingKeyError, match="API Key is required"):
        await prowl.verify_key()


@pytest.mark.asyncio
async def test_async_retrieve_token_success(mock_api: respx.Router) -> None:
    """Test successful token retrieval."""
    mock_api.get(url="/retrieve/token").mock(return_value=Response(status_code=200, text=TOKEN_RESPONSE))

    result = await AsyncProwl(apikey=VALID_API_KEY).retrieve_token(providerkey=VALID_PROVIDER_KEY)
    assert "token" in result
    assert result["token"] == VALID_TOKEN


@pytest.mark.asyncio
async def test_async_retrieve_token_success_providerkey_init(mock_api: respx.Router) -> None:
    """Test successful token retrieval."""
    mock_api.get(url="/retrieve/token").mock(return_value=Response(status_code=200, text=TOKEN_RESPONSE))

    result = await AsyncProwl(apikey=VALID_API_KEY, providerkey=VALID_PROVIDER_KEY).retrieve_token()
    assert "token" in result
    assert result["token"] == VALID_TOKEN


@pytest.mark.asyncio
async def test_async_retrieve_apikey_success(mock_api: respx.Router) -> None:
    """Test successful API key retrieval."""
    mock_api.get(url="/retrieve/apikey").mock(return_value=Response(status_code=200, text=APIKEY_RESPONSE))

    result = await AsyncProwl(apikey=VALID_API_KEY).retrieve_apikey(providerkey=VALID_PROVIDER_KEY, token=VALID_TOKEN)
    assert "apikey" in result
    assert result["apikey"] == VALID_API_KEY


@pytest.mark.asyncio
async def test_async_retrieve_apikey_success_providerkey_init(mock_api: respx.Router) -> None:
    """Test successful API key retrieval."""
    mock_api.get(url="/retrieve/apikey").mock(return_value=Response(status_code=200, text=APIKEY_RESPONSE))

    result = await AsyncProwl(apikey=VALID_API_KEY, providerkey=VALID_PROVIDER_KEY).retrieve_apikey(token=VALID_TOKEN)
    assert "apikey" in result
    assert result["apikey"] == VALID_API_KEY


@pytest.mark.asyncio
async def test_async_retrieve_token_missing_provider_key(mock_api: respx.Router) -> None:
    """Test token retrieval without provider key."""
    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=MissingKeyError, match="Provider Key is required"):
        await prowl.retrieve_token()


@pytest.mark.asyncio
async def test_async_retrieve_token_error(mock_api: respx.Router) -> None:
    """Test error in token retrieval."""
    mock_api.get(url="/retrieve/token").mock(return_value=Response(status_code=400, text="Bad Request"))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=APIError, match="Bad Request"):
        await prowl.retrieve_token(providerkey=VALID_PROVIDER_KEY)


@pytest.mark.asyncio
async def test_async_retrieve_apikey_error(mock_api: respx.Router) -> None:
    """Test error in API key retrieval."""
    mock_api.get(url="/retrieve/apikey").mock(return_value=Response(status_code=400, text="Bad Request"))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=APIError, match="Bad Request"):
        await prowl.retrieve_apikey(providerkey=VALID_PROVIDER_KEY, token=VALID_TOKEN)


@pytest.mark.asyncio
async def test_async_retrieve_apikey_missing_provider_key(mock_api: respx.Router) -> None:
    """Test API key retrieval without provider key."""
    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=MissingKeyError, match="Provider Key is required"):
        await prowl.retrieve_apikey(providerkey="", token=VALID_TOKEN)


@pytest.mark.asyncio
async def test_async_retrieve_apikey_missing_token(mock_api: respx.Router) -> None:
    """Test API key retrieval without token."""
    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=MissingKeyError, match="Token is required"):
        await prowl.retrieve_apikey(providerkey=VALID_PROVIDER_KEY, token="")


@pytest.mark.asyncio
async def test_async_retrieve_token_invalid_xml(mock_api: respx.Router) -> None:
    """Test retrieve_token with invalid XML response."""
    mock_api.get(url="/retrieve/token").mock(return_value=Response(status_code=200, text=INVALID_XML_RESPONSE))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=KeyError):
        await prowl.retrieve_token(providerkey=VALID_PROVIDER_KEY)


@pytest.mark.asyncio
async def test_async_retrieve_apikey_invalid_xml(mock_api: respx.Router) -> None:
    """Test retrieve_apikey with invalid XML response."""
    mock_api.get(url="/retrieve/apikey").mock(return_value=Response(status_code=200, text=INVALID_XML_RESPONSE))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=KeyError):
        await prowl.retrieve_apikey(providerkey=VALID_PROVIDER_KEY, token=VALID_TOKEN)


@pytest.mark.asyncio
async def test_async_post_unknown_error(mock_api: respx.Router) -> None:
    """Test post with unknown error code."""
    mock_api.post(url="/add").mock(return_value=Response(status_code=418, text="I'm a teapot"))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=APIError, match="Unknown API error: Error code 418"):
        await prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )


@pytest.mark.asyncio
async def test_async_post_rate_limit_error(mock_api: respx.Router) -> None:
    """Test post with rate limit error."""
    mock_api.post(url="/add").mock(return_value=Response(status_code=406, text="Rate limit exceeded"))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=APIError, match="Not accepted: Your IP address has exceeded the API limit"):
        await prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )


@pytest.mark.asyncio
async def test_async_post_not_approved_error(mock_api: respx.Router) -> None:
    """Test post with not approved error."""
    mock_api.post(url="/add").mock(return_value=Response(status_code=409, text="Not approved"))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(
        expected_exception=APIError,
        match="Not approved: The user has yet to approve your retrieve request",
    ):
        await prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )


@pytest.mark.asyncio
async def test_async_post_server_error(mock_api: respx.Router) -> None:
    """Test post with server error."""
    mock_api.post(url="/add").mock(return_value=Response(status_code=500, text="Internal Server Error"))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=APIError, match="Internal server error"):
        await prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )


@pytest.mark.asyncio
async def test_async_post_network_error(mock_api: respx.Router) -> None:
    """Test post with network error."""
    mock_api.post(url="/add").mock(side_effect=TransportError("Connection error"))

    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=APIError, match="API connection error: Connection error"):
        await prowl.post(
            application="Test App",
            event="Test Event",
            description="Test Description",
        )


@pytest.mark.asyncio
async def test_async_make_request_invalid_method() -> None:
    """Test if invalid method passed to _make_request."""
    prowl = AsyncProwl(apikey=VALID_API_KEY)
    with pytest.raises(expected_exception=ValueError, match="Invalid method type"):
        await prowl._make_request(method="invalid", url="/post", data={"providerkey": VALID_PROVIDER_KEY})  # noqa: SLF001


@pytest.mark.asyncio
async def test_async_client_passthrough(mock_api: respx.Router) -> None:
    """Test with client passed through to library."""
    mock_api.post(url="/add").mock(return_value=Response(status_code=200, text=SUCCESS_RESPONSE))

    client = AsyncClient()
    prowl = AsyncProwl(apikey=VALID_API_KEY, client=client)
    await prowl.post(application="Test App", event="Test Event", description="Test Description")
