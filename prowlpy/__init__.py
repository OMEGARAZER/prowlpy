"""
Prowlpy is a python module that implements the public api of Prowl to send push notification to iPhones.

Based on Prowlpy by Jacob Burch, Olivier Hevieu and Ken Pepple.

Typical usage:
    from prowlpy import Prowl
    p = Prowl("ApiKey")
    p.post(application="My App", event="Important Event", description="Successful Event")
"""

from .prowlpy import APIError, MissingKeyError, Prowl

try:
    from ._cli import main
except ImportError:

    def main() -> None:  # noqa: D103
        import sys  # noqa: PLC0415

        print(  # noqa: T201
            "The Prowlpy command line client could not be run because the required dependencies were not installed.\n"
            "Make sure it is installed with pip install prowlpy[cli]",
        )
        sys.exit(1)


__all__: list[str] = ["APIError", "MissingKeyError", "Prowl", "main"]
