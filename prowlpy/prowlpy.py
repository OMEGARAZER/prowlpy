"""
Prowlpy is a python library that implements the public api of Prowl to send push notification to iPhones.

Based on Prowlpy by Jacob Burch, Olivier Hevieu and Ken Pepple.

Typical usage:
    from prowlpy import Prowl
    p = Prowl(apikey="1234567890123456789012345678901234567890")
    p.post(application="My App", event="Important Event", description="Successful Event")
"""

import types
from typing import Any, NoReturn

import httpx
import xmltodict

__version__: str = "1.1.2"


class APIError(Exception):
    """Prowl API error base class."""


class BadRequestError(APIError):
    """Bad Request: The parameters you provided did not validate."""


class InvalidAPIKeyError(APIError):
    """Invalid API key."""


class RateLimitExceededError(APIError):
    """Not accepted: Your IP address has exceeded the API limit."""


class NotApprovedError(APIError):
    """Not approved: The user has yet to approve your retrieve request."""


class MissingKeyError(Exception):
    """Missing required key(s)."""


class ProwlpyCore:
    """Base class used to build synchronous and asynchronus classes, not intended for direct use."""

    def __init__(self, apikey: str | list[str] | None = None, providerkey: str | None = None) -> None:
        """Initialize the ProwlpyCore object.

        Args:
            apikey (str): Your Prowl API key.
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.

        Raises:
            MissingKeyError: If an API Key or Provider Key are not provided
        """
        if not apikey and not providerkey:
            raise MissingKeyError("API Key or Provider Key are required.")
        if isinstance(apikey, list | tuple):
            self.apikey = ",".join(apikey)
        else:
            self.apikey = apikey  # type: ignore[assignment]
        self.providerkey = providerkey
        self.headers = httpx.Headers(
            headers={
                "User-Agent": f"Prowlpy/{__version__}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        self.baseurl = "https://api.prowlapp.com/publicapi"

    def _api_error_handler(self, error_code: int, reason: str = "") -> NoReturn:
        """
        Raise an exception based on the error code from Prowl API.

        Errors from http://www.prowlapp.com/api.php

        Raises:
            BadRequestError: The parameters you provided did not validate.
            InvalidAPIKeyError: Invalid API key: apikey.
            RateLimitExceededError: Not accepted: Your IP address has exceeded the API limit.
            NotApprovedError: Not approved: The user has yet to approve your retrieve request.
            APIError: Internal server error.
        """
        if reason:
            reason = f" - {reason}"
        if error_code == 400:
            raise BadRequestError(f"Bad Request: The parameters you provided did not validate{reason}")
        if error_code == 401:
            raise InvalidAPIKeyError(f"Invalid API key: {self.apikey}{reason}")
        if error_code == 406:
            raise RateLimitExceededError(f"Not accepted: Your IP address has exceeded the API limit{reason}")
        if error_code == 409:
            raise NotApprovedError(f"Not approved: The user has yet to approve your retrieve request{reason}")
        if error_code == 500:
            raise APIError(f"Internal server error{reason}")

        raise APIError(f"Unknown API error: Error code {error_code}")

    def _prepare_data(
        self,
        route: str,
        application: str | None = None,
        event: str | None = None,
        description: str | None = None,
        priority: int = 0,
        url: str | None = None,
        providerkey: str | None = None,
        token: str | None = None,
    ) -> dict[str, str | int]:
        """
        Prepare data params for the Prowl API.

        Args:
            route (str): API route to process params for:
                post: post route
                verify: verify api key route
                token: retrieve token route
                key: retrieve api key route
            application (str): The name of the application sending the notification.
            event (str): The event or subject of the notification.
            description (str): A description of the event.
            priority (int): The priority of the notification (-2 to 2, default 0).
            url (str): The URL to include in the notification.
            providerkey (str): Your provider API key.
            token (str): Registration token returned from retrieve_token.

        Returns:
            dict[str, str | int]

        Raises:
            MissingKeyError: If an Key or Token is not provided.
            ValueError: Missing event and description or invalid priority.
        """
        if not self.apikey and route in {"post", "verify"}:
            raise MissingKeyError("API Key is required.")
        data: dict[str, str | int | None] = {"apikey": self.apikey}
        if not application and route == "post":
            raise ValueError("Must provide application.")
        if not any([event, description]) and route == "post":
            raise ValueError("Must provide event, description or both.")
        if priority not in {-2, -1, 0, 1, 2} and route == "post":
            raise ValueError(f"Priority must be between -2 and 2, got {priority}")
        if route == "post":
            data |= {
                "application": application,
                "event": event,
                "description": description,
                "priority": priority,
                "url": url[0:512] if url else None,  # Prowl has a 512 character limit on the URL.
            }
        providerkey = providerkey or self.providerkey
        if not providerkey and route in {"token", "key"}:
            raise MissingKeyError("Provider Key is required.")
        data["providerkey"] = providerkey
        if not token and route == "key":
            raise MissingKeyError("Token is required to retrieve API Key.")
        data["token"] = token
        return {key: value for key, value in data.items() if value is not None}

    def _make_request(self, *args, **kwargs):  # pragma: no cover  # noqa: ANN002, ANN003, ANN202
        """
        Make request to Prowl API.

        Not implemented in ProwlpyCore, should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def post(self, *args, **kwargs):  # pragma: no cover  # noqa: ANN002, ANN003, ANN201
        """
        Push a notification to the Prowl API.

        Not implemented in ProwlpyCore, should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def verify_key(self, *args, **kwargs):  # pragma: no cover  # noqa: ANN002, ANN003, ANN201
        """
        Verify if the API key is valid.

        Not implemented in ProwlpyCore, should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def retrieve_token(self, *args, **kwargs):  # pragma: no cover  # noqa: ANN002, ANN003, ANN201
        """
        Retrieve a registration token to generate API key.

        Not implemented in ProwlpyCore, should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def retrieve_apikey(self, *args, **kwargs):  # pragma: no cover  # noqa: ANN002, ANN003, ANN201
        """
        Generate an API key from a registration token.

        Not implemented in ProwlpyCore, should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")


class Prowl(ProwlpyCore):
    """
    Communicate with the Prowl API.

    Args:
        apikey (str, required): Your Prowl API key.
        providerkey (str, optional): Your provider API key, only required if you are whitelisted.

    Methods:
        post: Push a notification to the Prowl API.
        verify_key: Verify if an API key is valid.
        retrieve_token: Retrieve a registration token to generate an API key.
        retrieve_apikey: Generate an API key from registration token.
    """

    def __init__(
        self,
        apikey: str | list[str] | None = None,
        providerkey: str | None = None,
        client: Any = None,  # noqa: ANN401
    ) -> None:
        """
        Initialize a Prowl object with an API key and optionally a Provider key.

        Args:
            apikey (str): Your Prowl API key.
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.
            client (optional): HTTP client if you would like to use your own. Must be compatible with the httpx api.
        """
        self.add = self.send = self.post
        super().__init__(apikey=apikey, providerkey=providerkey)
        self.client = client or httpx.Client(http2=True)

    def __enter__(self) -> "Prowl":
        """
        Context manager entry.

        Returns:
            Prowl: Prowl instance.
        """
        return self

    def __del__(self) -> None:
        """Context manager del."""
        self.close()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.close()
        if exc_type is not None:
            _info = (exc_type, exc_val, exc_tb)

    def close(self) -> None:
        """Context manager close."""
        if hasattr(self, "client"):
            self.client.close()

    def _make_request(self, method: str, url: str, data: dict[str, str | int]) -> httpx.Response:
        """
        Make request to Prowl API.

        Args:
            method (str): Request method, post/get
            url (str): API route suffix.
            data (dict): processed data params to send to the Prowl API.

        Returns:
            httpx.Response

        Raises:
            APIError: If unable to connect to the API.
            ValueError: If method is not provided.
        """
        if method.lower() not in {"post", "get"}:
            raise ValueError("Invalid method type. Must be 'post' or 'get'.")
        request_client = getattr(self.client, method.lower())
        try:
            response: httpx.Response = request_client(url=url, params=data, headers=self.headers)
            if not response.is_success:
                self._api_error_handler(response.status_code, response.text)
        except httpx.RequestError as error:
            raise APIError(f"API connection error: {error}") from error
        else:
            return response

    def post(
        self,
        application: str,
        event: str | None = None,
        description: str | None = None,
        priority: int = 0,
        providerkey: str | None = None,
        url: str | None = None,
    ) -> dict[str, str]:
        """
        Push a notification to the Prowl API.

        Must provide either event, description or both.

        Args:
            application (str): The name of the application sending the notification.
            event (str): The event or subject of the notification.
            description (str): A description of the event.
            priority (int, optional): The priority of the notification (-2 to 2, default 0).
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.
            url (str, optional): The URL to include in the notification.

        Returns:
            dict: {'code': '200', 'remaining': '999', 'resetdate': '1735714800'}

        """
        data: dict[str, str | int] = self._prepare_data(
            route="post",
            application=application,
            event=event,
            description=description,
            priority=priority,
            providerkey=providerkey,
            url=url,
        )

        response: httpx.Response = self._make_request(method="post", url=f"{self.baseurl}/add", data=data)

        return xmltodict.parse(xml_input=response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]

    def verify_key(self, providerkey: str | None = None) -> dict[str, str]:
        """
        Verify if the API key is valid.

        Args:
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.

        Returns:
            dict: {'code': '200', 'remaining': '999', 'resetdate': '1735714800'}
        """
        data: dict[str, str | int] = self._prepare_data(route="verify", providerkey=providerkey)

        response: httpx.Response = self._make_request(method="get", url=f"{self.baseurl}/verify", data=data)

        return xmltodict.parse(xml_input=response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]

    def retrieve_token(self, providerkey: str | None = None) -> dict[str, str]:
        """
        Retrieve a registration token to generate API key.

        Args:
            providerkey (str): Your provider API key.

        Returns:
            dict: {'token': '38528720c5f2f071300f2cc7e6b5a3fb3144761d',
                   'url': 'https://www.prowlapp.com/retrieve.php?token=38528720c5f2f071300f2cc7e6b5a3fb3144761d',
                   'code': '200',
                   'remaining': '999',
                   'resetdate': '1735714800'}
        """
        data: dict[str, str | int] = self._prepare_data(route="token", providerkey=providerkey)

        response: httpx.Response = self._make_request(method="get", url=f"{self.baseurl}/retrieve/token", data=data)

        parsed: dict[str, dict] = xmltodict.parse(xml_input=response.text, attr_prefix="", cdata_key="text")["prowl"]
        return parsed["retrieve"] | parsed["success"]

    def retrieve_apikey(self, token: str, providerkey: str | None = None) -> dict[str, str]:
        """
        Generate an API key from a registration token.

        Args:
            token (str): Registration token returned from retrieve_token.
            providerkey (str): Your provider API key.

        Returns:
            dict: {'apikey': '22b697c1c3cd23a38b33f7d34b5fd8b3bce02b35',
                   'code': '200',
                   'remaining': '999',
                   'resetdate': '1735714800'}
        """
        data: dict[str, str | int] = self._prepare_data(route="key", providerkey=providerkey, token=token)

        response: httpx.Response = self._make_request(method="get", url=f"{self.baseurl}retrieve/apikey", data=data)

        parsed: dict[str, dict] = xmltodict.parse(xml_input=response.text, attr_prefix="", cdata_key="text")["prowl"]
        return parsed["retrieve"] | parsed["success"]


class AsyncProwl(ProwlpyCore):
    """
    Asynchronously communicate with the Prowl API.

    Args:
        apikey (str, required): Your Prowl API key.
        providerkey (str, optional): Your provider API key, only required if you are whitelisted.

    Methods:
        post: Push a notification to the Prowl API.
        verify_key: Verify if an API key is valid.
        retrieve_token: Retrieve a registration token to generate an API key.
        retrieve_apikey: Generate an API key from registration token.
    """

    def __init__(
        self,
        apikey: str | list[str] | None = None,
        providerkey: str | None = None,
        client: Any = None,  # noqa: ANN401
    ) -> None:
        """
        Initialize an AsyncProwl object with an API key and optionally a Provider key.

        Args:
            apikey (str): Your Prowl API key.
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.
            client (optional): HTTP client if you would like to use your own. Must be compatible with the httpx api.
        """
        self.add = self.send = self.post
        super().__init__(apikey=apikey, providerkey=providerkey)
        self.client = client or httpx.AsyncClient(http2=True)

    async def __aenter__(self) -> "AsyncProwl":
        """
        Asyncronous context manager entry.

        Returns:
            AsyncProwl: Prowl instance.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Asyncronous context manager exit."""
        await self.aclose()
        if exc_type is not None:
            _info = (exc_type, exc_val, exc_tb)

    async def aclose(self) -> None:
        """Asyncronous context manager close."""
        if hasattr(self, "client"):
            await self.client.aclose()

    async def _make_request(self, method: str, url: str, data: dict[str, str | int]) -> httpx.Response:
        """
        Make request to Prowl API.

        Args:
            method (str): Request method, post/get
            url (str): API route suffix.
            data (dict): processed data params to send to the Prowl API.

        Returns:
            httpx.Response

        Raises:
            APIError: If unable to connect to the API.
            ValueError: If method is not provided.
        """
        if method.lower() not in {"post", "get"}:
            raise ValueError("Invalid method type. Must be 'post' or 'get'.")
        request_client = getattr(self.client, method.lower())
        try:
            response: httpx.Response = await request_client(url=url, params=data, headers=self.headers)
            if not response.is_success:
                self._api_error_handler(response.status_code, response.text)
        except httpx.RequestError as error:
            raise APIError(f"API connection error: {error}") from error
        else:
            return response

    async def post(
        self,
        application: str,
        event: str | None = None,
        description: str | None = None,
        priority: int = 0,
        providerkey: str | None = None,
        url: str | None = None,
    ) -> dict[str, str]:
        """
        Push a notification to the Prowl API.

        Must provide either event, description or both.

        Args:
            application (str): The name of the application sending the notification.
            event (str): The event or subject of the notification.
            description (str): A description of the event.
            priority (int, optional): The priority of the notification (-2 to 2, default 0).
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.
            url (str, optional): The URL to include in the notification.

        Returns:
            dict: {'code': '200', 'remaining': '999', 'resetdate': '1735714800'}
        """
        data: dict[str, str | int] = self._prepare_data(
            route="post",
            application=application,
            event=event,
            description=description,
            priority=priority,
            providerkey=providerkey,
            url=url,
        )

        response: httpx.Response = await self._make_request(method="post", url=f"{self.baseurl}/add", data=data)

        return xmltodict.parse(xml_input=response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]

    async def verify_key(self, providerkey: str | None = None) -> dict[str, str]:
        """
        Verify if the API key is valid.

        Args:
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.

        Returns:
            dict: {'code': '200', 'remaining': '999', 'resetdate': '1735714800'}
        """
        data: dict[str, str | int] = self._prepare_data(route="verify", providerkey=providerkey)

        response: httpx.Response = await self._make_request(method="get", url=f"{self.baseurl}/verify", data=data)

        return xmltodict.parse(xml_input=response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]

    async def retrieve_token(self, providerkey: str | None = None) -> dict[str, str]:
        """
        Retrieve a registration token to generate API key.

        Args:
            providerkey (str): Your provider API key.

        Returns:
            dict: {'token': '38528720c5f2f071300f2cc7e6b5a3fb3144761d',
                   'url': 'https://www.prowlapp.com/retrieve.php?token=38528720c5f2f071300f2cc7e6b5a3fb3144761d',
                   'code': '200',
                   'remaining': '999',
                   'resetdate': '1735714800'}
        """
        data: dict[str, str | int] = self._prepare_data(route="token", providerkey=providerkey)

        response: httpx.Response = await self._make_request(
            method="get",
            url=f"{self.baseurl}/retrieve/token",
            data=data,
        )

        parsed: dict[str, dict] = xmltodict.parse(xml_input=response.text, attr_prefix="", cdata_key="text")["prowl"]
        return parsed["retrieve"] | parsed["success"]

    async def retrieve_apikey(self, token: str, providerkey: str | None = None) -> dict[str, str]:
        """
        Generate an API key from a registration token.

        Args:
            token (str): Registration token returned from retrieve_token.
            providerkey (str): Your provider API key.

        Returns:
            dict: {'apikey': '22b697c1c3cd23a38b33f7d34b5fd8b3bce02b35',
                   'code': '200',
                   'remaining': '999',
                   'resetdate': '1735714800'}
        """
        data: dict[str, str | int] = self._prepare_data(route="key", providerkey=providerkey, token=token)

        response: httpx.Response = await self._make_request(
            method="get",
            url=f"{self.baseurl}retrieve/apikey",
            data=data,
        )

        parsed: dict[str, dict] = xmltodict.parse(xml_input=response.text, attr_prefix="", cdata_key="text")["prowl"]
        return parsed["retrieve"] | parsed["success"]
