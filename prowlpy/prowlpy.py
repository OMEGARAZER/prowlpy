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


class APIError(Exception):
    """Prowl API error."""


class MissingKeyError(Exception):
    """Missing required key(s)."""


class Prowl:
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
        self.headers = httpx.Headers({
            "User-Agent": f"Prowlpy/{__version__}",
            "Content-Type": "application/x-www-form-urlencoded",
        })
        self.client = httpx.Client(base_url="https://api.prowlapp.com/publicapi", headers=self.headers, http2=True)

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

    def _api_error_handler(self, error_code: int, reason: str = "") -> NoReturn:
        """
        Raise an exception based on the error code from Prowl API.

        Errors from http://www.prowlapp.com/api.php

        Raises:
            APIError:
                400: Bad Request: The parameters you provided did not validate.
                401: Invalid API key: apikey.
                406: Not accepted: Your IP address has exceeded the API limit.
                409: Not approved: The user has yet to approve your retrieve request.
                500: Internal server error.
        """  # noqa: DOC502
        exception = f"Unknown API error: Error code {error_code}"
        if error_code == 400:
            exception = "Bad Request: The parameters you provided did not validate"
        if error_code == 401:
            exception = f"Invalid API key: {self.apikey}"
        if error_code == 406:
            exception = "Not accepted: Your IP address has exceeded the API limit"
        if error_code == 409:
            exception = "Not approved: The user has yet to approve your retrieve request"
        if error_code == 500:
            exception = "Internal server error"
        if reason:
            exception = f"{exception} - {reason}"

        raise APIError(exception)

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
        data = {key: value for key, value in data.items() if value is not None}

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
            raise MissingKeyError("Provider key is required to retrieve API key.")
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
