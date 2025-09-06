"""
Prowlpy is a python library that implements the public api of Prowl to send push notification to iPhones.

Based on Prowlpy by Jacob Burch, Olivier Hevieu and Ken Pepple.

Typical usage:
    from prowlpy import Prowl
    p = Prowl(apikey="1234567890123456789012345678901234567890")
    p.post(application="My App", event="Important Event", description="Successful Event")
"""

import types
from typing import NoReturn

import httpx
import xmltodict

__version__ = "1.0.1"
BASEURL = "https://api.prowlapp.com/publicapi"


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


class BaseProwl:
    """
    Base class for Prowl API communication.

    This class is not intended to be used directly, but as a base for synchronous and asynchronous implementations.
    """

    def __init__(self, apikey: str | list[str] | None = None, providerkey: str | None = None) -> None:
        """
        Initialize a BaseProwl object with an API key and optionally a Provider key.

        Args:
            apikey (str | list[str]): Your Prowl API key.
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.

        Raises:
            MissingKeyError: If an API Key or Provider Key are not provided.
        """
        self.add = self.send = self.post
        if not apikey and not providerkey:
            raise MissingKeyError("API Key or Provider Key are required.")
        if isinstance(apikey, list | tuple):
            self.apikey = ",".join(apikey)
        else:
            self.apikey = apikey
        self.providerkey = providerkey

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

    def _prepare_post_data(
        self,
        application: str,
        event: str | None = None,
        description: str | None = None,
        priority: int = 0,
        providerkey: str | None = None,
        url: str | None = None,
    ) -> dict:
        """
        Do all the data preparation for the post method.

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

        Raises:
            MissingKeyError: If an API Key is not provided.
            ValueError: Missing event and description or invalid priority.
        """
        if not self.apikey:
            raise MissingKeyError("API Key is required.")
        if not application:
            raise ValueError("Must provide application.")
        if not any([event, description]):
            raise ValueError("Must provide event, description or both.")
        if priority not in {-2, -1, 0, 1, 2}:
            raise ValueError(f"Priority must be between -2 and 2, got {priority}")
        data = {
            "apikey": self.apikey,
            "application": application,
            "event": event,
            "description": description,
            "priority": priority,
        }
        if providerkey:
            data["providerkey"] = providerkey
        elif self.providerkey:
            data["providerkey"] = self.providerkey
        if url:
            data["url"] = url[0:512]  # Prowl has a 512 character limit on the URL.
        return {key: value for key, value in data.items() if value is not None}

    def post(self, *args, **kwargs): # pragma: no cover
        raise NotImplementedError("This method should be implemented in subclasses.")

    def verify_key(self, *args, **kwargs): # pragma: no cover
        raise NotImplementedError("This method should be implemented in subclasses.")

    def retrieve_token(self, *args, **kwargs): # pragma: no cover
        raise NotImplementedError("This method should be implemented in subclasses.")

    def retrieve_apikey(self, *args, **kwargs): # pragma: no cover
        raise NotImplementedError("This method should be implemented in subclasses.")


class AsyncProwl(BaseProwl):
    """
    Communicate asynchronously with the Prowl API.

    Args:
        apikey (str, required): Your Prowl API key.
        providerkey (str, optional): Your provider API key, only required if you are whitelisted.

    Methods:
        post: Push a notification to the Prowl API.
        verify_key: Verify if an API key is valid.
        retrieve_token: Retrieve a registration token to generate an API key.
        retrieve_apikey: Generate an API key from registration token.
    """
    def __init__(self, apikey: str | list[str] | None = None, providerkey: str | None = None) -> None:
        """
        Initialize a Prowl object with an API key and optionally a Provider key.

        Args:
            apikey (str): Your Prowl API key.
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.
        """
        self.headers = httpx.Headers({
            "User-Agent": f"Prowlpy/{__version__}",
            "Content-Type": "application/x-www-form-urlencoded",
        })
        self.client = httpx.AsyncClient(base_url=BASEURL, headers=self.headers, http2=True)
        super().__init__(apikey, providerkey)

    async def __aenter__(self) -> "AsyncProwl":
        """
        Asynchronous context manager entry.

        Returns:
            Prowl: Prowl instance.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Asynchronous context manager exit."""
        await self.aclose()
        if exc_type is not None:
            _info = (exc_type, exc_val, exc_tb)

    async def aclose(self) -> None:
        """Asynchronous context manager close."""
        if hasattr(self, "client"):
            await self.client.aclose()

    async def post(
        self,
        application: str,
        event: str | None = None,
        description: str | None = None,
        priority: int = 0,
        providerkey: str | None = None,
        url: str | None = None,
    ) -> dict:
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

        Raises:
            MissingKeyError: If an API Key is not provided.
            ValueError: Missing event and description or invalid priority.
            APIError: If unable to connect to the API.
        """
        data = self._prepare_post_data(application, event, description, priority, providerkey, url)
        try:
            response = await self.client.post("/add", params=data)
            if not response.is_success:
                self._api_error_handler(response.status_code, response.text)
        except httpx.RequestError as error:
            raise APIError(f"API connection error: {error}") from error

        return xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]

    async def verify_key(self, providerkey: str | None = None) -> dict:
        """
        Verify if the API key is valid.

        Args:
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.

        Returns:
            dict: {'code': '200', 'remaining': '999', 'resetdate': '1735714800'}

        Raises:
            MissingKeyError: If an API Key is not provided.
        """
        if not self.apikey:
            raise MissingKeyError("API Key is required.")
        data = {"apikey": self.apikey}
        if providerkey:
            data["providerkey"] = providerkey
        elif self.providerkey:
            data["providerkey"] = self.providerkey

        response = await self.client.get("/verify", params=data)

        if not response.is_success:
            self._api_error_handler(response.status_code)

        return xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]

    async def retrieve_token(self, providerkey: str | None = None) -> dict:
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

        Raises:
            MissingKeyError: If Provider key is missing.
        """
        data = {}
        if self.apikey:
            data["apikey"] = self.apikey
        if providerkey:
            data["providerkey"] = providerkey
        elif self.providerkey:
            data["providerkey"] = self.providerkey
        else:
            raise MissingKeyError("Provider key is required to retrieve Token.")

        response = await self.client.get("/retrieve/token", params=data)

        if not response.is_success:
            self._api_error_handler(response.status_code)

        rateinfo = xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]
        token = xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["retrieve"]
        return token | rateinfo

    async def retrieve_apikey(self, token: str, providerkey: str | None = None) -> dict:
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

        Raises:
            MissingKeyError: If provider key or token are missing.
        """
        data = {}
        if self.apikey:
            data["apikey"] = self.apikey
        if providerkey:
            data["providerkey"] = providerkey
        elif self.providerkey:
            data["providerkey"] = self.providerkey
        else:
            raise MissingKeyError("Provider key is required to retrieve Token.")

        if token:
            data["token"] = token
        else:
            raise MissingKeyError("Token is required to retrieve API key. Call retrieve_teken to request it.")

        response = await self.client.get("retrieve/apikey", params=data)

        if not response.is_success:
            self._api_error_handler(response.status_code)

        rateinfo = xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]
        apikey = xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["retrieve"]
        return apikey | rateinfo


class Prowl(BaseProwl):
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

    def __init__(self, apikey: str | list[str] | None = None, providerkey: str | None = None) -> None:
        """
        Initialize a Prowl object with an API key and optionally a Provider key.

        Args:
            apikey (str): Your Prowl API key.
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.
        """
        self.headers = httpx.Headers({
            "User-Agent": f"Prowlpy/{__version__}",
            "Content-Type": "application/x-www-form-urlencoded",
        })
        self.client = httpx.Client(base_url=BASEURL, headers=self.headers, http2=True)
        super().__init__(apikey, providerkey)

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

    def post(
        self,
        application: str,
        event: str | None = None,
        description: str | None = None,
        priority: int = 0,
        providerkey: str | None = None,
        url: str | None = None,
    ) -> dict:
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

        Raises:
            MissingKeyError: If an API Key is not provided.
            ValueError: Missing event and description or invalid priority.
            APIError: If unable to connect to the API.
        """
        data = self._prepare_post_data(application, event, description, priority, providerkey, url)
        try:
            response = self.client.post("/add", params=data)
            if not response.is_success:
                self._api_error_handler(response.status_code, response.text)
        except httpx.RequestError as error:
            raise APIError(f"API connection error: {error}") from error

        return xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]

    def verify_key(self, providerkey: str | None = None) -> dict:
        """
        Verify if the API key is valid.

        Args:
            providerkey (str, optional): Your provider API key, only required if you are whitelisted.

        Returns:
            dict: {'code': '200', 'remaining': '999', 'resetdate': '1735714800'}

        Raises:
            MissingKeyError: If an API Key is not provided.
        """
        if not self.apikey:
            raise MissingKeyError("API Key is required.")
        data = {"apikey": self.apikey}
        if providerkey:
            data["providerkey"] = providerkey
        elif self.providerkey:
            data["providerkey"] = self.providerkey

        response = self.client.get("/verify", params=data)

        if not response.is_success:
            self._api_error_handler(response.status_code)

        return xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]

    def retrieve_token(self, providerkey: str | None = None) -> dict:
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

        Raises:
            MissingKeyError: If Provider key is missing.
        """
        data = {}
        if self.apikey:
            data["apikey"] = self.apikey
        if providerkey:
            data["providerkey"] = providerkey
        elif self.providerkey:
            data["providerkey"] = self.providerkey
        else:
            raise MissingKeyError("Provider key is required to retrieve Token.")

        response = self.client.get("/retrieve/token", params=data)

        if not response.is_success:
            self._api_error_handler(response.status_code)

        rateinfo = xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]
        token = xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["retrieve"]
        return token | rateinfo

    def retrieve_apikey(self, token: str, providerkey: str | None = None) -> dict:
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

        Raises:
            MissingKeyError: If provider key or token are missing.
        """
        data = {}
        if self.apikey:
            data["apikey"] = self.apikey
        if providerkey:
            data["providerkey"] = providerkey
        elif self.providerkey:
            data["providerkey"] = self.providerkey
        else:
            raise MissingKeyError("Provider key is required to retrieve Token.")

        if token:
            data["token"] = token
        else:
            raise MissingKeyError("Token is required to retrieve API key. Call retrieve_teken to request it.")

        response = self.client.get("retrieve/apikey", params=data)

        if not response.is_success:
            self._api_error_handler(response.status_code)

        rateinfo = xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["success"]
        apikey = xmltodict.parse(response.text, attr_prefix="", cdata_key="text")["prowl"]["retrieve"]
        return apikey | rateinfo
