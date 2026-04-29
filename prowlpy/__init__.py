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

__all__: list[str] = [
    "APIError",
    "AsyncProwl",
    "BadRequestError",
    "InvalidAPIKeyError",
    "MissingKeyError",
    "NotApprovedError",
    "Prowl",
    "RateLimitExceededError",
]
