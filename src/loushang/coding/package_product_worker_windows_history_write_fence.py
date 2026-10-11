"""Refuse legacy Windows Worker writes once a history cutover is visible.

The cutover owner is not published yet. This guard is deliberately one-way:
until each writer has a base-aware successor, a committed or staged owner
record must stop old-file writes under the Product GC gate.
"""

from __future__ import annotations

from loushang.harness.resources.packages.plugin_lifecycle.windows_quarantine import (
    windows_listdir_at,
)

WINDOWS_WORKER_HISTORY_CUTOVER_NAME = "worker-history-cutover-v1.json"


def require_windows_worker_legacy_history_writable(root: int) -> None:
    """Call with a pinned Product root and its GC write gate held."""

    if type(root) is not int or root < 0:
        raise ValueError("Windows Worker history root is invalid")
    names = windows_listdir_at(root)
    if any(
        name.casefold().lstrip(".").startswith(WINDOWS_WORKER_HISTORY_CUTOVER_NAME)
        for name in names
    ):
        raise ValueError("Windows Worker legacy history cutover is present")


__all__ = [
    "WINDOWS_WORKER_HISTORY_CUTOVER_NAME",
    "require_windows_worker_legacy_history_writable",
]
