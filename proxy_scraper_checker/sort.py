from __future__ import annotations

from typing import Tuple

from .proxy import Proxy


def protocol_sort_key(proxy: Proxy) -> int:
    return proxy.protocol.value  # type: ignore[no-any-return]


def natural_sort_key(proxy: Proxy) -> Tuple[int, ...]:
    return (proxy.protocol.value, *map(int, proxy.host.split(".")), proxy.port)


def timeout_sort_key(proxy: Proxy) -> float:
    return proxy.timeout
