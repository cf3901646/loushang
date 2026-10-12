from __future__ import annotations

import asyncio
import threading

import pytest

from loushang.harness.resources._catalog_preview_tasks import CatalogPreviewTaskError
from loushang.harness.resources.loader import (
    ResourceLoader,
    ResourceLoaderCompatibilityError,
)


async def _entered(event: threading.Event) -> None:
    async with asyncio.timeout(5):
        while not event.is_set():
            await asyncio.sleep(0.001)


def test_last_view_close_releases_waiter_before_native_settlement(tmp_path, monkeypatch) -> None:
    loader = ResourceLoader(user_resource_roots=())
    view = loader.create_catalog_session_view()
    original = ResourceLoader._compute_catalog_input_receipt_from_state
    entered, released = threading.Event(), threading.Event()

    def compute(*args, **kwargs):
        entered.set()
        assert released.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(ResourceLoader, "_compute_catalog_input_receipt_from_state", staticmethod(compute))

    async def scenario():
        waiter = asyncio.create_task(_request(view, tmp_path))
        try:
            await _entered(entered)
            await view.aclose()
            with pytest.raises(asyncio.CancelledError):
                await waiter
            assert not released.is_set()
            assert not view._catalog_preview_waiters
            with pytest.raises(ResourceLoaderCompatibilityError, match="settlement_pending"):
                loader.close()
            released.set()
            await loader.aclose()
            assert not loader._catalog_preview_tasks._jobs
        finally:
            released.set()
            waiter.cancel()
            await loader.aclose()
            await asyncio.gather(waiter, return_exceptions=True)

    asyncio.run(scenario())


def _request(loader, root, *, subject="a" * 64, policy="b" * 64, units=4096):
    return loader.preview_catalog_input_fingerprint(
        root, subject_digest=subject, policy_digest=policy,
        max_work_units=units, time_budget_seconds=30,
    )


def test_resource_waiters_share_scan_and_cancel_only_their_own_reference(tmp_path, monkeypatch) -> None:
    loader = ResourceLoader(user_resource_roots=())
    original = ResourceLoader._compute_catalog_input_receipt_from_state
    entered, released = threading.Event(), threading.Event()
    calls = 0

    def compute(*args, **kwargs):
        nonlocal calls
        calls += 1
        entered.set()
        assert released.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(ResourceLoader, "_compute_catalog_input_receipt_from_state", staticmethod(compute))

    async def scenario():
        first = asyncio.create_task(_request(loader, tmp_path))
        second = asyncio.create_task(_request(loader, tmp_path))
        try:
            await _entered(entered)
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
            assert calls == 1
            assert not second.done()
            released.set()
            fingerprint = await second
            assert len(fingerprint) == 64
            assert fingerprint == loader.preview_catalog_input_receipt(tmp_path).input_fingerprint
            assert loader._catalog_authority_selected is False
            assert loader._legacy_authority_selected is False
        finally:
            released.set()
            await loader.aclose()
            await asyncio.gather(first, second, return_exceptions=True)

    asyncio.run(scenario())


def test_resource_close_joins_actual_native_completion_even_when_close_is_cancelled(tmp_path, monkeypatch) -> None:
    loader = ResourceLoader(user_resource_roots=())
    original = ResourceLoader._compute_catalog_input_receipt_from_state
    entered, released = threading.Event(), threading.Event()

    def compute(*args, **kwargs):
        entered.set()
        assert released.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(ResourceLoader, "_compute_catalog_input_receipt_from_state", staticmethod(compute))

    async def scenario():
        waiter = asyncio.create_task(_request(loader, tmp_path))
        closing = None
        try:
            await _entered(entered)
            with pytest.raises(ResourceLoaderCompatibilityError, match="settlement_pending"):
                loader.close()
            closing = asyncio.create_task(loader.aclose())
            await asyncio.sleep(0)
            closing.cancel()
            await asyncio.sleep(0)
            assert not closing.done()
            released.set()
            with pytest.raises(asyncio.CancelledError):
                await closing
            with pytest.raises(CatalogPreviewTaskError, match="catalog_preview_closed"):
                await waiter
            loader.close()
        finally:
            released.set()
            await loader.aclose()
            await asyncio.gather(waiter, *(() if closing is None else (closing,)), return_exceptions=True)

    asyncio.run(scenario())


def test_resource_background_budget_exhaustion_is_discardable(tmp_path) -> None:
    loader = ResourceLoader(user_resource_roots=())

    async def scenario():
        try:
            with pytest.raises(CatalogPreviewTaskError, match="work_budget_exceeded"):
                await _request(loader, tmp_path, units=1)
            assert loader._catalog_authority_selected is False
            assert loader._legacy_authority_selected is False
            assert len(await _request(loader, tmp_path)) == 64
        finally:
            await loader.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("domain", ("subject", "policy"))
def test_resource_background_jobs_do_not_cross_isolation_domains(tmp_path, monkeypatch, domain) -> None:
    loader = ResourceLoader(user_resource_roots=())
    original = ResourceLoader._compute_catalog_input_receipt_from_state
    entered, released = threading.Event(), threading.Event()
    counter_lock = threading.Lock()
    calls = 0

    def compute(*args, **kwargs):
        nonlocal calls
        with counter_lock:
            calls += 1
            if calls == 2:
                entered.set()
        assert released.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(ResourceLoader, "_compute_catalog_input_receipt_from_state", staticmethod(compute))

    async def scenario():
        first = asyncio.create_task(_request(loader, tmp_path))
        second = asyncio.create_task(_request(loader, tmp_path, **{domain: "c" * 64}))
        try:
            await _entered(entered)
            assert calls == 2
            released.set()
            assert await first == await second
        finally:
            released.set()
            await loader.aclose()
            await asyncio.gather(first, second, return_exceptions=True)

    asyncio.run(scenario())


def test_resource_background_result_rejects_configuration_changed_during_scan(tmp_path, monkeypatch) -> None:
    loader = ResourceLoader(user_resource_roots=())
    original = ResourceLoader._compute_catalog_input_receipt_from_state
    entered, released = threading.Event(), threading.Event()

    def compute(*args, **kwargs):
        entered.set()
        assert released.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(ResourceLoader, "_compute_catalog_input_receipt_from_state", staticmethod(compute))

    async def scenario():
        waiter = asyncio.create_task(_request(loader, tmp_path))
        try:
            await _entered(entered)
            loader.set_runtime_options(no_skills=True)
            released.set()
            with pytest.raises(ResourceLoaderCompatibilityError, match="catalog_preview_stale"):
                await waiter
        finally:
            released.set()
            await loader.aclose()
            await asyncio.gather(waiter, return_exceptions=True)

    asyncio.run(scenario())


def test_failed_native_submission_does_not_admit_queued_source_reads(tmp_path, monkeypatch) -> None:
    from loushang.harness.resources import _catalog_preview_tasks as tasks

    loader = ResourceLoader(user_resource_roots=())
    accepted = []
    original_executor = tasks._EXECUTOR
    monkeypatch.setattr(tasks, "_SUBMISSION_FENCED", threading.Event())

    class LostSubmissionReceipt:
        def submit(self, operation):
            accepted.append(original_executor.submit(operation))
            raise RuntimeError("receipt lost after enqueue")

    def forbidden_read(*args, **kwargs):
        pytest.fail("failed native submission admitted source reads")

    monkeypatch.setattr(tasks, "_EXECUTOR", LostSubmissionReceipt())
    monkeypatch.setattr(ResourceLoader, "_compute_catalog_input_receipt_from_state", staticmethod(forbidden_read))

    async def scenario():
        try:
            with pytest.raises(RuntimeError, match="receipt lost after enqueue"):
                await _request(loader, tmp_path)
            with pytest.raises(CatalogPreviewTaskError, match="scheduler_unavailable"):
                await _request(loader, tmp_path)
        finally:
            await loader.aclose()

    asyncio.run(scenario())
    assert len(accepted) == 1
    assert accepted[0].result(timeout=5) is None


def test_process_preview_capacity_rejects_extra_work_without_changing_peers(tmp_path, monkeypatch) -> None:
    loader = ResourceLoader(user_resource_roots=())
    original = ResourceLoader._compute_catalog_input_receipt_from_state
    entered, released = threading.Event(), threading.Event()

    def compute(*args, **kwargs):
        entered.set()
        assert released.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(ResourceLoader, "_compute_catalog_input_receipt_from_state", staticmethod(compute))

    async def scenario():
        waiters = [asyncio.create_task(_request(loader, tmp_path, policy=f"{index:064x}")) for index in range(8)]
        try:
            await _entered(entered)
            with pytest.raises(CatalogPreviewTaskError, match="capacity_exceeded"):
                await _request(loader, tmp_path, policy=f"{8:064x}")
            released.set()
            fingerprints = await asyncio.gather(*waiters)
            assert len(set(fingerprints)) == 1
        finally:
            released.set()
            await loader.aclose()
            await asyncio.gather(*waiters, return_exceptions=True)

    asyncio.run(scenario())


def test_background_read_pin_survives_mount_retirement_and_closes_at_native_completion(tmp_path, monkeypatch) -> None:
    from loushang.harness.resources.packages.mounts import PackageResourceMount
    from loushang.harness.resources.plugins.manifest import PluginManifestParser
    from loushang.harness.resources.plugins.revisions import PluginRevisionStore

    source = tmp_path / "source"
    prompts = source / "resources" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "review.md").write_text("review", encoding="utf-8")
    (source / "plugin.json").write_text('{"name":"review-pack","packageRoot":"resources"}', encoding="utf-8")
    published = PluginRevisionStore(tmp_path / "revisions").publish(PluginManifestParser().parse(source))
    handle = published.revision_handle
    assert handle is not None
    loader = ResourceLoader(user_resource_roots=())
    loader.set_package_mounts((PackageResourceMount(
        root=published.package_root, content_digest=published.content_digest,
        revision_handle=handle,
    ),))
    pins = []
    original_acquire = handle.acquire_readonly_capture

    def acquire():
        pin = original_acquire()
        pins.append(pin)
        return pin

    monkeypatch.setattr(handle, "acquire_readonly_capture", acquire)
    original_compute = ResourceLoader._compute_catalog_input_receipt_from_state
    entered, released = threading.Event(), threading.Event()

    def compute(*args, **kwargs):
        entered.set()
        assert released.wait(5)
        return original_compute(*args, **kwargs)

    monkeypatch.setattr(ResourceLoader, "_compute_catalog_input_receipt_from_state", staticmethod(compute))

    async def scenario():
        waiter = asyncio.create_task(_request(loader, tmp_path))
        try:
            await _entered(entered)
            assert len(pins) == 1
            loader.set_package_mounts(())
            assert handle.closed is True
            assert pins[0].closed is False
            released.set()
            with pytest.raises(ResourceLoaderCompatibilityError, match="catalog_preview_stale"):
                await waiter
            assert pins[0].closed is True
        finally:
            released.set()
            await loader.aclose()
            await asyncio.gather(waiter, return_exceptions=True)

    asyncio.run(scenario())
