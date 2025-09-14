"""
Prowlpy is a python module that implements the public api of Prowl to send push notification to iPhones.

Based on Prowlpy by Jacob Burch, Olivier Hevieu and Ken Pepple.

Typical usage:
    from prowlpy import Prowl
    p = Prowl("ApiKey")
    p.post(application="My App", event="Important Event", description="Successful Event")
"""

from .prowlpy import (
    APIError,
    AsyncProwl,
    BadRequestError,
    InvalidAPIKeyError,
    MissingKeyError,
    NotApprovedError,
    Prowl,
    RateLimitExceededError,
)

try:
    from ._cli import main
except ImportError:

    def main() -> None:  # type: ignore[misc]
        """Fallback main if cli components not installed."""
        import sys  # noqa: PLC0415

        print(  # noqa: T201
            "The Prowlpy command line client could not be run because the required dependencies were not installed.\n"
            "Make sure it is installed with pip install prowlpy[cli]",
        )
        sys.exit(1)


__all__: list[str] = [
    "APIError",
    "AsyncProwl",
    "BadRequestError",
    "InvalidAPIKeyError",
    "MissingKeyError",
    "NotApprovedError",
    "Prowl",
    "RateLimitExceededError",
    "main",
]
