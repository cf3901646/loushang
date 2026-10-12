"""Deterministically partition collected pytest cases across CI jobs."""

from __future__ import annotations

from hashlib import sha256

import pytest


def shard_for_nodeid(nodeid: str, shards: int) -> int:
    if shards < 1:
        raise ValueError("shard count must be positive")
    digest = sha256(nodeid.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % shards


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("loushang-ci-shard")
    group.addoption("--ci-shard-index", type=int)
    group.addoption("--ci-shard-count", type=int)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    index = config.getoption("ci_shard_index")
    count = config.getoption("ci_shard_count")
    if index is None and count is None:
        return
    if count is None or index is None or count < 1 or not 0 <= index < count:
        raise pytest.UsageError("invalid CI pytest shard index/count")
    selected = []
    deselected = []
    for item in items:
        (selected if shard_for_nodeid(item.nodeid, count) == index else deselected).append(item)
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected
