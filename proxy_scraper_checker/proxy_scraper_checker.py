from __future__ import annotations

import asyncio
import itertools
import json
import logging
from collections import Counter
from random import shuffle
from shutil import rmtree
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import aiofiles
import aiofiles.os
import aiofiles.ospath
import attrs
import maxminddb
from aiohttp import ClientResponse, ClientSession, ClientTimeout, hdrs
from aiohttp_socks import ProxyType
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskID,
    TextColumn,
)
from rich.table import Table

from . import sort
from .constants import CACHE_DIR, GEODB_ETAG_PATH, GEODB_PATH, GEODB_URL
from .null_context import NullContext
from .parsers import PROXY_REGEX
from .proxy import Proxy
from .settings import Settings
from .utils import bytes_decode, is_url

if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison

logger = logging.getLogger(__name__)


async def read_etag() -> Optional[str]:
    try:
        async with aiofiles.open(GEODB_ETAG_PATH, "rb") as etag_file:
            content = await etag_file.read()
    except FileNotFoundError:
        return None
    return bytes_decode(content)


async def save_etag(etag: Optional[str]) -> None:
    if etag:
        async with aiofiles.open(
            GEODB_ETAG_PATH, "w", encoding="utf-8"
        ) as etag_file:
            await etag_file.write(etag)


async def save_geodb(
    r: ClientResponse, *, progress: Progress, task: TaskID
) -> None:
    async with aiofiles.open(GEODB_PATH, "wb") as geodb:
        async for chunk in r.content.iter_any():
            await geodb.write(chunk)
            progress.update(task, advance=len(chunk))


async def download_geodb(session: ClientSession, progress: Progress) -> None:
    headers = None
    if await aiofiles.ospath.exists(GEODB_PATH):
        current_etag = await read_etag()
        if current_etag:
            headers = {hdrs.IF_NONE_MATCH: current_etag}

    async with session.get(
        GEODB_URL, headers=headers, raise_for_status=True
    ) as r:
        if r.status == 304:  # noqa: PLR2004
            logger.info(
                "Latest geolocation database is already cached at %s",
                GEODB_PATH,
            )
            return
        await save_geodb(
            r,
            progress=progress,
            task=progress.add_task(
                "[yellow]Downloader[red] :: [green]GeoDB",
                total=r.content_length,
            ),
        )
    await save_etag(r.headers.get(hdrs.ETAG))


def create_proxy_list_str(
    *, include_protocol: bool, proxies: Sequence[Proxy], anonymous_only: bool
) -> str:
    return "\n".join(
        proxy.as_str(include_protocol=include_protocol)
        for proxy in proxies
        if not anonymous_only or proxy.host != proxy.exit_ip
    )


@attrs.define(
    repr=False,
    weakref_slot=False,
    kw_only=True,
    eq=False,
    getstate_setstate=False,
    match_args=False,
)
class ProxyScraperChecker:
    console: Console
    proxies_count: Dict[ProxyType, int] = attrs.field(init=False, factory=dict)
    proxies: Set[Proxy] = attrs.field(init=False, factory=set)
    session: ClientSession
    settings: Settings

    async def fetch_source(
        self,
        *,
        source: str,
        proto: ProxyType,
        progress: Progress,
        task: TaskID,
        timeout: ClientTimeout,
    ) -> None:
        try:
            if is_url(source):
                async with self.session.get(
                    source, timeout=timeout
                ) as response:
                    await response.read()
                text = await response.text()
            else:
                response = None
                async with aiofiles.open(source, "rb") as f:
                    content = await f.read()
                text = bytes_decode(content)
        except asyncio.TimeoutError:
            logger.warning("%s | Timed out", source)
        except Exception as e:
            e_str = str(e)
            args: Tuple[object, ...] = (
                (
                    "%s | %s.%s (%s)",
                    source,
                    e.__class__.__module__,
                    e.__class__.__qualname__,
                    e_str,
                )
                if e_str
                else (
                    "%s | %s.%s",
                    source,
                    e.__class__.__module__,
                    e.__class__.__qualname__,
                )
            )
            logger.error(*args)
        else:
            proxies = PROXY_REGEX.finditer(text)
            try:
                proxy = next(proxies)
            except StopIteration:
                args = (
                    ("%s | No proxies found", source)
                    if not response or response.status == 200  # noqa: PLR2004
                    else ("%s | HTTP status code %d", source, response.status)
                )
                logger.warning(*args)
            else:
                for proxy in itertools.chain((proxy,), proxies):  # noqa: B020
                    try:
                        protocol = ProxyType[proxy.group("protocol").upper()]
                    except (AttributeError, KeyError):
                        protocol = proto
                    self.proxies.add(
                        Proxy(
                            protocol=protocol,
                            host=proxy.group("host"),
                            port=int(proxy.group("port")),
                            username=proxy.group("username"),
                            password=proxy.group("password"),
                        )
                    )
        progress.update(task, advance=1)

    async def check_proxy(
        self, *, proxy: Proxy, progress: Progress, task: TaskID
    ) -> None:
        try:
            await proxy.check(self.settings)
        except Exception as e:
            # Too many open files
            if isinstance(e, OSError) and e.errno == 24:  # noqa: PLR2004
                logger.error("Please, set max_connections to lower value.")

            logger.debug(
                "%s.%s | %s",
                e.__class__.__module__,
                e.__class__.__qualname__,
                e,
            )
            self.proxies.remove(proxy)
        progress.update(task, advance=1)

    async def fetch_all_sources(self, progress: Progress) -> None:
        tasks = {
            proto: progress.add_task(
                f"[yellow]Scraper [red]:: [green]{proto.name}",
                total=len(sources),
            )
            for proto, sources in self.settings.sources.items()
        }
        timeout = ClientTimeout(total=self.settings.source_timeout)
        coroutines = (
            self.fetch_source(
                source=source,
                proto=proto,
                progress=progress,
                task=tasks[proto],
                timeout=timeout,
            )
            for proto, sources in self.settings.sources.items()
            for source in sources
        )
        await asyncio.gather(*coroutines)
        self.proxies_count = self.get_current_proxies_count()

    async def check_all_proxies(self, progress: Progress) -> None:
        tasks = {
            proto: progress.add_task(
                f"[yellow]Checker [red]:: [green]{proto.name}", total=count
            )
            for proto, count in self.get_current_proxies_count().items()
        }
        coroutines = [
            self.check_proxy(
                proxy=proxy, progress=progress, task=tasks[proxy.protocol]
            )
            for proxy in self.proxies
        ]
        shuffle(coroutines)
        await asyncio.gather(*coroutines)

    @aiofiles.ospath.wrap
    def save_proxies(self) -> None:
        sorted_proxies = self.get_sorted_proxies(
            sort_key=self.settings.sorting_key
        )
        if self.settings.output_json:
            mmdb: Union[maxminddb.Reader, NullContext] = (
                maxminddb.open_database(GEODB_PATH)
                if self.settings.enable_geolocation
                else NullContext()
            )
            self.settings.output_path.mkdir(parents=True, exist_ok=True)
            with mmdb as mmdb_reader:
                proxy_dicts = [
                    {
                        "protocol": proxy.protocol.name.lower(),
                        "username": proxy.username,
                        "password": proxy.password,
                        "host": proxy.host,
                        "port": proxy.port,
                        "exit_ip": proxy.exit_ip,
                        "timeout": round(proxy.timeout, 2),
                        "geolocation": mmdb_reader.get(proxy.exit_ip)
                        if mmdb_reader is not None
                        else None,
                    }
                    for proxy in sorted(self.proxies, key=sort.timeout_sort_key)
                ]
                with (self.settings.output_path / "proxies.json").open(
                    "w", encoding="utf-8"
                ) as f:
                    json.dump(
                        proxy_dicts,
                        f,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                with (self.settings.output_path / "proxies_pretty.json").open(
                    "w", encoding="utf-8"
                ) as f:
                    json.dump(proxy_dicts, f, ensure_ascii=False, indent="\t")

        if self.settings.output_txt:
            grouped_proxies = tuple(
                (k, sorted(v, key=self.settings.sorting_key))
                for k, v in self.get_grouped_proxies().items()
            )

            for folder, anonymous_only in (
                (self.settings.output_path / "proxies", False),
                (self.settings.output_path / "proxies_anonymous", True),
            ):
                try:
                    rmtree(folder)
                except FileNotFoundError:
                    pass
                folder.mkdir(parents=True, exist_ok=True)
                text = create_proxy_list_str(
                    proxies=sorted_proxies,
                    anonymous_only=anonymous_only,
                    include_protocol=True,
                )
                (folder / "all.txt").write_text(text, encoding="utf-8")
                for proto, proxies in grouped_proxies:
                    text = create_proxy_list_str(
                        proxies=proxies,
                        anonymous_only=anonymous_only,
                        include_protocol=False,
                    )
                    (
                        folder / f"{ProxyType(proto).name.lower()}.txt"
                    ).write_text(text, encoding="utf-8")
        logger.info(
            "Proxies have been saved at %s.",
            self.settings.output_path.absolute(),
        )

    async def run(self) -> None:
        if self.settings.enable_geolocation:
            await aiofiles.os.makedirs(CACHE_DIR, exist_ok=True)
        with self._get_progress_bar() as progress:
            fetch = self.fetch_all_sources(progress)
            if self.settings.enable_geolocation:
                await asyncio.gather(
                    fetch, download_geodb(self.session, progress)
                )
            else:
                await fetch
            await self.check_all_proxies(progress)

        table = self._get_results_table()
        self.console.print(table)

        await self.save_proxies()

        logger.info(
            "Thank you for using "
            "https://github.com/monosans/proxy-scraper-checker :)"
        )

    def _get_results_table(self) -> Table:
        table = Table()
        table.add_column("Protocol", style="cyan")
        table.add_column("Working", style="magenta")
        table.add_column("Total", style="green")
        for proto, proxies in self.get_grouped_proxies().items():
            working = len(tuple(proxies))
            total = self.proxies_count[ProxyType(proto)]
            percentage = working / total if total else 0
            table.add_row(
                ProxyType(proto).name,
                f"{working} ({percentage:.1%})",
                str(total),
            )
        return table

    def _get_progress_bar(self) -> Progress:
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=self.console,
        )

    def get_grouped_proxies(self) -> Dict[ProxyType, Tuple[Proxy, ...]]:
        key = sort.protocol_sort_key
        return {
            **{proto: () for proto in self.settings.sources},
            **{
                ProxyType(k): tuple(v)
                for k, v in itertools.groupby(
                    sorted(self.proxies, key=key), key=key
                )
            },
        }

    def get_sorted_proxies(
        self,
        sort_key: Callable[
            [Proxy], SupportsRichComparison
        ] = sort.protocol_sort_key,
    ) -> List[Proxy]:
        return sorted(self.proxies, key=sort_key)

    def get_current_proxies_count(self) -> Dict[ProxyType, int]:
        return dict(Counter(proxy.protocol for proxy in self.proxies))
