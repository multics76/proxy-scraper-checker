from __future__ import annotations

from urllib.parse import urlparse

import charset_normalizer
from aiohttp import ClientResponse


def is_url(value: str) -> bool:
    parsed_url = urlparse(value)
    return bool(parsed_url.scheme and parsed_url.netloc)


def bytes_decode(b: bytes) -> str:
    return str(charset_normalizer.from_bytes(b)[0])


def fallback_charset_resolver(r: ClientResponse, b: bytes) -> str:  # noqa: ARG001
    return charset_normalizer.from_bytes(b)[0].encoding
