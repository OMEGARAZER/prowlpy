"""Prowlpy CLI module."""

import sys

import click
from httpx import Client
from loguru import logger

from .prowlpy import APIError, MissingKeyError, Prowl, __version__

logger.configure(handlers=[{"sink": sys.stdout, "format": "{message}", "level": "INFO"}])


def _check_version(context: click.Context, _param: click.Parameter, value: bool) -> None:
    if not value or context.resilient_parsing:
        return
    try:
        with Client(base_url="https://pypi.org/pypi", http2=True) as client:
            latest: str = client.get(url="/prowlpy/json").json()["info"]["version"]
            logger.info("You are currently using v{} the latest is v{}", __version__, latest)
    except TimeoutError:
        logger.info("Timeout reached fetching current version from Pypi - Prowlpy v{}", __version__)
    context.exit()


def _help(context: click.Context, _param: click.Parameter, value: bool) -> None:
    if not value or context.resilient_parsing:
        return
    print_help()
    context.exit()


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


@click.command(add_help_option=False)
@click.option("apikey", "--apikey", "-k", type=str, multiple=True)
@click.option("application", "--application", "-a", type=str, default=None)
@click.option("event", "--event", "-e", type=str, default=None)
@click.option("description", "--description", "-d", type=str, default=None)
@click.option("priority", "--priority", "-p", type=click.IntRange(min=-2, max=2, clamp=True), default=0)
@click.option("url", "--url", "-u", type=str, default=None)
@click.option("version", "--version", "-v", is_flag=True, is_eager=True, expose_value=False, callback=_check_version)
@click.option("help", "--help", "-h", is_flag=True, is_eager=True, expose_value=False, callback=_help)
@click.pass_context
def main(
    context: click.Context,
    apikey: str,
    application: str,
    event: str,
    description: str,
    priority: int,
    url: str,
) -> None:
    if len(sys.argv) == 1:
        print_help()
        context.exit(code=1)
    try:
        with Prowl(apikey=apikey) as prowl:
            response: dict[str, str] = prowl.send(
                application=application,
                event=event,
                description=description,
                priority=priority,
                url=url,
            )
            logger.info("Message sent, rate limit remaining {}", response["remaining"])
    except (APIError, MissingKeyError, ValueError) as e:
        logger.info(e)
        sys.exit(1)
