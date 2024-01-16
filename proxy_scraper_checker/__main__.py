from __future__ import annotations

import asyncio
import logging
import sys
from typing import TYPE_CHECKING, Dict

import aiofiles
import rich.traceback
from aiohttp import ClientSession, TCPConnector
from rich.console import Console
from rich.logging import RichHandler

from . import constants, utils
from .proxy_scraper_checker import ProxyScraperChecker
from .settings import Settings
from .typing_compat import Any

if sys.version_info >= (3, 11):
    try:
        import tomllib
    except ImportError:
        # Help users on older alphas
        if not TYPE_CHECKING:
            import tomli as tomllib
else:
    import tomli as tomllib


def set_event_loop_policy() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    elif sys.implementation.name == "cpython" and sys.platform in {
        "darwin",
        "linux",
    }:
        try:
            import uvloop  # noqa: PLC0415
        except ImportError:
            pass
        else:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def configure_logging(console: Console, *, debug: bool) -> None:
    rich.traceback.install(
        console=console, width=None, extra_lines=0, word_wrap=True
    )
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(message)s",
        datefmt=logging.Formatter.default_time_format,
        handlers=(
            RichHandler(
                console=console,
                omit_repeated_times=False,
                show_path=False,
                rich_tracebacks=True,
                tracebacks_extra_lines=0,
            ),
        ),
    )


async def read_config(file: str) -> Dict[str, Any]:
    async with aiofiles.open(file, "rb") as f:
        content = await f.read()
    return tomllib.loads(utils.bytes_decode(content))


async def main() -> None:
    cfg = await read_config("config.toml")
    console = Console()
    configure_logging(console, debug=cfg["debug"])

    async with ClientSession(
        connector=TCPConnector(ssl=constants.SSL_CONTEXT),
        cookie_jar=constants.get_cookie_jar(),
        fallback_charset_resolver=utils.fallback_charset_resolver,
    ) as s:
        settings = await Settings.from_dict(cfg, session=s)
        await ProxyScraperChecker(
            console=console, session=s, settings=settings
        ).run()


if __name__ == "__main__":
    set_event_loop_policy()
    asyncio.run(main())
