"""Bounded native computation owned by the Resource Catalog preview scope."""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Callable
from concurrent.futures import CancelledError, ThreadPoolExecutor
from dataclasses import dataclass
from typing import cast

_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="resource-preview")
_SLOTS = threading.BoundedSemaphore(8)
_SUBMISSION_FENCED = threading.Event()


class CatalogPreviewTaskError(RuntimeError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass(eq=False)
class _Job:
    key: object
    receipt: asyncio.Future[tuple[bool, object]]
    cancelled: threading.Event
    references: int = 0


class CatalogPreviewTaskScope:
    """Keep native completion separate from cancellation of a Session waiter.

    Jobs retain only a pure computation and its temporary read pins. No result
    constitutes Resource selection, Writer admission, or execution authority.
    The process shares two native slots and at most eight admitted jobs.
    """

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._jobs: list[_Job] = []
        self._closed = False

    def _on_loop(self) -> asyncio.AbstractEventLoop:
        loop = asyncio.get_running_loop()
        if self._loop is None:
            self._loop = loop
        elif self._loop is not loop:
            raise CatalogPreviewTaskError("catalog_preview_loop_changed")
        return loop

    async def run(
        self, key: object,
        prepare: Callable[[], tuple[Callable[[Callable[[], None]], str], Callable[[], None]]], *,
        max_work_units: int, time_budget_seconds: float,
    ) -> str:
        loop = self._on_loop()
        if self._closed:
            raise CatalogPreviewTaskError("catalog_preview_closed")
        if _SUBMISSION_FENCED.is_set():
            raise CatalogPreviewTaskError("catalog_preview_scheduler_unavailable")
        job = next((item for item in self._jobs if item.key == key and not item.cancelled.is_set()), None)
        if job is None:
            if not _SLOTS.acquire(blocking=False):
                raise CatalogPreviewTaskError("catalog_preview_capacity_exceeded")
            try:
                operation, dispose = prepare()
            except BaseException:
                _SLOTS.release()
                raise
            job = _Job(key, loop.create_future(), threading.Event())
            self._jobs.append(job)
            selected = job
            deadline = time.monotonic() + time_budget_seconds
            units = 0
            published = threading.Event()
            admitted = False

            def probe() -> None:
                nonlocal units
                if selected.cancelled.is_set():
                    raise CancelledError("Catalog preview reference released")
                units += 1
                if units > max_work_units:
                    raise CatalogPreviewTaskError("catalog_preview_work_budget_exceeded")
                if time.monotonic() > deadline:
                    raise CatalogPreviewTaskError("catalog_preview_time_budget_exceeded")

            def publish(outcome: tuple[bool, object]) -> None:
                selected.receipt.set_result(outcome)
                if selected.references == 0:
                    self._jobs.remove(selected)

            def native() -> None:
                published.wait()
                if not admitted:
                    return  # Unknown submission never admits source reads.
                try:
                    try:
                        outcome: tuple[bool, object] = (True, operation(probe))
                    finally:
                        dispose()
                except BaseException as error:
                    outcome = (False, error)
                finally:
                    _SLOTS.release()
                loop.call_soon_threadsafe(publish, outcome)

            try:
                _EXECUTOR.submit(native)
                admitted = True
            except BaseException as error:
                # submit may throw after queue admission. The publication gate
                # proves the queued callback cannot read or close these pins.
                _SUBMISSION_FENCED.set()
                selected.cancelled.set()
                try:
                    dispose()
                except BaseException as cleanup_error:
                    error.add_note(f"preview pin cleanup failed: {type(cleanup_error).__name__}")
                self._jobs.remove(selected)
                _SLOTS.release()
                raise
            finally:
                published.set()
        if job.references >= 64:
            raise CatalogPreviewTaskError("catalog_preview_reference_capacity_exceeded")
        job.references += 1
        try:
            succeeded, value = await asyncio.shield(job.receipt)
            if self._closed:
                raise CatalogPreviewTaskError("catalog_preview_closed")
            if not succeeded:
                raise cast(BaseException, value)
            return cast(str, value)
        finally:
            job.references -= 1
            if job.references == 0:
                job.cancelled.set()
                if job.receipt.done():
                    self._jobs.remove(job)

    def fence(self) -> bool:
        """Stop new references; return whether actual native work is settled."""

        self._closed = True
        for job in self._jobs:
            job.cancelled.set()
        return all(job.receipt.done() for job in self._jobs)

    async def close(self) -> None:
        self._on_loop()
        self.fence()
        cancellation: asyncio.CancelledError | None = None
        for job in tuple(self._jobs):
            while not job.receipt.done():
                try:
                    await asyncio.shield(job.receipt)
                except asyncio.CancelledError as error:
                    cancellation = error
        if cancellation is not None:
            raise cancellation
