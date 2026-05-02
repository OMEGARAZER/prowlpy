"""Prowlpy CLI module."""

import sys
from typing import Annotated

try:
    import typer
    from loguru import logger
    from pyreqwest.client import SyncClientBuilder
    from pyreqwest.exceptions import RequestTimeoutError
except ImportError:
    print(  # noqa: T201
        "The Prowlpy command line client could not be run because the required dependencies were not installed.\n"
        "Make sure it is installed with pip install prowlpy[cli] if you used pip to install.",
    )
    sys.exit(1)

from .prowlpy import APIError, MissingKeyError, Prowl, __version__

logger.configure(handlers=[{"sink": sys.stdout, "format": "{message}", "level": "INFO"}])


def _check_version(context: typer.Context, value: bool) -> None:
    if not value or context.resilient_parsing:
        return
    try:
        with (
            SyncClientBuilder()
            .error_for_status(enable=True)
            .base_url(url="https://pypi.org/")
            .http2(enable=True)
            .build() as client
        ):
            latest: str = client.get(url="pypi/prowlpy/json").build().send().json()["info"]["version"]
            logger.info("You are currently using v{} the latest is v{}", __version__, latest)
    except RequestTimeoutError:
        logger.info("Timeout reached fetching current version from Pypi - Prowlpy v{}", __version__)
    raise typer.Exit(code=0)


def _help(context: typer.Context, value: bool) -> None:
    if not value or context.resilient_parsing:
        return
    print_help()
    raise typer.Exit(code=0)


def print_help() -> None:
    hlogger = logger.opt(colors=True)
    hlogger.info("\t<r><b>Prowlpy</b></r>\n")
    hlogger.info("Use Prowlpy to send messages through the Prowl API.\n")
    hlogger.info(
        "Usage: prowlpy --apikey <cyan>[api key]</cyan> --application <cyan>[app name]</cyan> "
        "--description <cyan>[description text]</cyan>\n\n",
    )
    hlogger.info("  --apikey, -k  <cyan>[api key]</cyan>\t\tAPI key(s) to send notification to (required).")
    hlogger.info("  --application, -a  <cyan>[app name]</cyan>\t\tApp name to use for notification (required).")
    hlogger.info(
        "  --event, -e  <cyan>[event name]</cyan>\t\tThe event or subject of the notification "
        "(optional if description is given).",
    )
    hlogger.info(
        "  --description, -d  <cyan>[text]</cyan>\t\tLong description for the notification "
        "(optional if event is given).",
    )
    hlogger.info(
        "  --priority, -p  <cyan>[priority]</cyan>\t\tPriority to send the notification between -2 [lowest] and "
        "2 [highest] (default 0).",
    )
    hlogger.info("  --url, -u  <cyan>[url]</cyan>\t\t\tURL to attach to the notification (optional).")
    hlogger.info("  --version, -v\t\t\t\tDisplays current version and checks for the latest version on pypi.")
    hlogger.info("  --help, -h\t\t\t\tDisplays this help message. You are here.")


app = typer.Typer()


@app.command(add_help_option=False)
def main(
    apikey: Annotated[list[str] | None, typer.Option("--apikey", "-k")] = None,
    application: Annotated[str, typer.Option("--application", "-a")] = "",
    event: Annotated[str | None, typer.Option("--event", "-e")] = None,
    description: Annotated[str | None, typer.Option("--description", "-d")] = None,
    priority: Annotated[int, typer.Option("--priority", "-p", min=-2, max=2, clamp=True)] = 0,
    url: Annotated[str | None, typer.Option("--url", "-u")] = None,
    *,
    _version: Annotated[
        bool,
        typer.Option("--version", "-v", callback=_check_version, is_eager=True, expose_value=False),
    ] = False,
    _custom_help: Annotated[
        bool,
        typer.Option("--help", "-h", callback=_help, is_eager=True, expose_value=False),
    ] = False,
) -> None:
    if len(sys.argv) == 1:
        print_help()
        raise typer.Exit(code=1)
    try:
        with Prowl(apikey=apikey) as prowl:
            response: dict[str, str] = prowl.post(
                application=application,
                event=event,
                description=description,
                priority=priority,
                url=url,
            )
            logger.info("Message sent, rate limit remaining {}", response["remaining"])
    except (APIError, MissingKeyError, ValueError) as e:
        logger.info(e)
        raise typer.Exit(code=1) from e
