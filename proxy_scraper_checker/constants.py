from __future__ import annotations

import ssl
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

import certifi
import platformdirs
from aiohttp import DummyCookieJar, hdrs

GEODB_URL = "https://raw.githubusercontent.com/P3TERX/GeoLite.mmdb/download/GeoLite2-City.mmdb"
CACHE_DIR = platformdirs.user_cache_dir("proxy_scraper_checker")
GEODB_PATH = Path(CACHE_DIR, "GeoLite2-City.mmdb")
GEODB_ETAG_PATH = Path(CACHE_DIR, "GeoLite2-City.mmdb.etag")
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

HEADERS: MappingProxyType[str, str] = MappingProxyType({
    hdrs.USER_AGENT: (
        "Mozilla/5.0 (Windows NT 10.0; rv:121.0) Gecko/20100101 Firefox/121.0"
    )
})


@lru_cache(None)
def get_cookie_jar() -> DummyCookieJar:
    return DummyCookieJar()
