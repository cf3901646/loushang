from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime

import pytest

from loushang.ai.types import UserMessage
from loushang.coding import bootstrap
from loushang.coding.composition_sets import resolve_coding_composition_set
from loushang.coding.package_product_runtime import (
    CodingFencedProductApplicationSelection,
)
from loushang.coding.resume_activation_attempt import (
    CodingActivationAttemptV1,
    CodingResumeRecoveryRequired,
)
from loushang.coding.resume_activation_plan import build_session_activation_plan
from loushang.coding.resume_continuation import CodingResumeContinuationCleanupFailure
from loushang.coding.resume_permission_confirmation import (
    CodingResumePermissionConfirmation,
    coding_resume_permission_request,
)
from loushang.coding.runtime.agent_session_runtime import AgentSessionRuntime
from loushang.coding.session.agent_session import AgentSession
from loushang.coding.session_manager import SessionManager
from loushang.harness.approval import DenyApprovalResolver, InteractiveApprovalResolver
from loushang.harness.session.lifecycle import PreparedSessionOperationStateError
from loushang.harness.transcript.jsonl_file import load_agent_transcript_file

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux owned Resume Writer")


@pytest.mark.parametrize("mode", ["admitted", "denied", "invalid_check", "revoked_after_selection"])
def test_first_resume_prepares_original_epoch_without_session_lease(tmp_path, monkeypatch, mode):
    monkeypatch.setenv("LOUSHANG_HOME", str(tmp_path / "home"))
    selection = CodingFencedProductApplicationSelection()
    calls = []

    def admission():
        calls.append(True)
        if mode == "denied" or (mode == "revoked_after_selection" and len(calls) == 2):
            raise PermissionError("current caller revoked")
        if mode == "invalid_check":
            return True
        return None

    before = tuple(tmp_path.rglob("*"))
    try:
        if mode in {"denied", "invalid_check"}:
            error = PermissionError if mode == "denied" else TypeError
            with pytest.raises(error):
                selection.prepare_resume_epoch(tmp_path, require_current_admission=admission)
            assert not selection._owners
            assert tuple(tmp_path.rglob("*")) == before
            assert len(calls) == 1
        else:
            if mode == "revoked_after_selection":
                with pytest.raises(PermissionError, match="revoked"):
                    selection.prepare_resume_epoch(tmp_path, require_current_admission=admission)
            else:
                fingerprint = selection.prepare_resume_epoch(tmp_path, require_current_admission=admission)
                assert fingerprint == selection.resume_epoch_fingerprint(tmp_path)
            assert len(calls) == 2
            assert len(selection._owners) == 1
            owner = selection._owners[tmp_path].epoch_runtime
            # The original native registry, rather than a local mock lease
            # counter, proves no Session runtime admission was performed.
            with owner.registry.exclusive_runtime_quiescence(store_id=owner.registry.store_id) as receipt:
                assert receipt.active_runtime_lease_ids == ()
    finally:
        selection.close()
    assert not selection._owners


def test_selected_resume_epoch_is_native_readonly_and_never_repairs_tail(tmp_path, monkeypatch):
    import os

    from loushang.harness.resources.packages.plugin_lifecycle.epoch_fence import (
        PackageEpochFenceError,
    )

    async def scenario():
        selection = CodingFencedProductApplicationSelection()
        with pytest.raises(RuntimeError, match="unavailable"):
            selection.resume_epoch_fingerprint(tmp_path)
        assert not selection._owners
        manager = await SessionManager.new(session_dir=tmp_path / "sessions", cwd=str(tmp_path), persist=False)
        factory = None
        try:
            factory = selection.factory_for_session(manager)
            assert factory is not None
            owner = selection._owners[tmp_path].epoch_runtime
            journal = owner.control_root / "epoch.jsonl"
            original = journal.read_bytes()
            before = {path: path.stat().st_mtime_ns for path in tmp_path.rglob("*")}
            opened = os.open

            def readonly_open(path, flags, *args, **kwargs):
                assert not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
                return opened(path, flags, *args, **kwargs)

            with monkeypatch.context() as guard:
                # This forwarding wrapper preserves the real dir_fd support;
                # keep capability detection accurate while forbidding writes.
                assert opened in os.supports_dir_fd
                guard.setattr(os, "supports_dir_fd", os.supports_dir_fd | {readonly_open})
                guard.setattr(os, "open", readonly_open)
                first = selection.resume_epoch_fingerprint(tmp_path)
                assert len(first) == 64
                assert selection.resume_epoch_fingerprint(tmp_path) == first
            assert journal.read_bytes() == original
            assert {path: path.stat().st_mtime_ns for path in tmp_path.rglob("*")} == before
            assert len(selection._owners) == 1
            foreign = tmp_path / "foreign"
            foreign.mkdir()
            with pytest.raises(RuntimeError, match="unavailable"):
                selection.resume_epoch_fingerprint(foreign)
            journal.write_bytes(original + b'{"incomplete":')
            try:
                with monkeypatch.context() as guard:
                    guard.setattr(os, "supports_dir_fd", os.supports_dir_fd | {readonly_open})
                    guard.setattr(os, "open", readonly_open)
                    with pytest.raises(PackageEpochFenceError):
                        selection.resume_epoch_fingerprint(tmp_path)
                assert journal.read_bytes() == original + b'{"incomplete":'
            finally:
                journal.write_bytes(original)
            factory.runtime_lease.release()
            factory = None
            owner.close()
            with pytest.raises(ValueError, match="closed"):
                selection.resume_epoch_fingerprint(tmp_path)
            selection.fence()
            with pytest.raises(RuntimeError, match="unavailable"):
                selection.resume_epoch_fingerprint(tmp_path)
        finally:
            if factory is not None:
                factory.runtime_lease.release()
            selection.close()
            await manager.dispose_runtime_profile()

    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["consume", "first_epoch_prepared", "delivered_close_failed", "abort", "stale", "root_close", "cancel_prepare", "cancel_delivery", "delivery_revoked", "abort_failed", "host_bind_failed", "cleanup_debt", "epoch_mismatch", "epoch_unselected", "epoch_fenced"])
def test_root_owns_native_resume_preparation_and_delivery(tmp_path, monkeypatch, mode):
    monkeypatch.setenv("LOUSHANG_HOME", str(tmp_path / "home"))

    async def scenario():
        manager = await SessionManager.new(
            session_dir=tmp_path / "sessions", cwd=str(tmp_path), defer_materialization=False,
        )
        await manager.append_message(UserMessage(role="user", content="history", timestamp=1.0))
        path = manager.session_file
        header = manager.header
        selection = CodingFencedProductApplicationSelection()
        if mode not in {"epoch_unselected", "first_epoch_prepared"}:
            factory = selection.factory_for_session(manager)
            assert factory is not None
            factory.runtime_lease.release()
        await manager.dispose_runtime_profile()
        assert path is not None

        def ordinary_factory(manager, **kwargs):
            return bootstrap.create_agent_session(
                session_manager=manager, composition_set="coding-minimal", no_tools=True,
                package_product_runtime_factory=selection.factory_for_session(manager), **kwargs,
            )

        root = AgentSessionRuntime(
            session_dir=tmp_path / "sessions", session_factory=ordinary_factory,
            owned_transcripts=True, product_owner_selection=selection,
        )
        issuer = InteractiveApprovalResolver(fallback=DenyApprovalResolver())
        prepared = None
        task = None
        entered = asyncio.Event()
        native_sessions = []
        try:
            before = path.read_bytes()
            selected_owners = dict(selection._owners)
            history = await root.preview_resume_history(path)
            assert path.read_bytes() == before
            assert selection._owners == selected_owners
            assert root.current_session is None
            plan = build_session_activation_plan(
                history, resolve_coding_composition_set("coding-minimal"), workspace_root=tmp_path,
            )
            if mode == "first_epoch_prepared":
                # Exercise formal native epoch preparation after pure history,
                # without any throwaway Session/lease. This callback is an
                # orchestration fixture, not a production actor/Policy proof.
                def caller_current():
                    assert root.current_session is None
                    assert not root._owned_transcript_factory.pending_preparations

                selection.prepare_resume_epoch(tmp_path, require_current_admission=caller_current)
                assert path.read_bytes() == before
            attempt = CodingActivationAttemptV1(
                attempt_id="root-attempt", request_id="root-input", session_id=header.conversation_id,
                original_leaf_id=plan.selected_leaf_id, ancestry_digest=plan.ancestry_digest,
                plan_fingerprint=plan.plan_id,
                epoch_fingerprint=("a" * 64 if mode in {"epoch_mismatch", "epoch_unselected"}
                                   else selection.resume_epoch_fingerprint(tmp_path)),
                subject_digest="b" * 64,
            )

            async def confirm(payload):
                assert root.current_session is None
                assert await issuer.handle_result(payload["action_id"], outcome="allow_once")

            issuer.set_request_presenter(confirm)
            fact = await issuer.confirm(coding_resume_permission_request(
                attempt, actor_id="root", expansion_codes=("authority.unknown",),
            ))
            assert fact is not None
            permission = CodingResumePermissionConfirmation(
                attempt, "root", ("authority.unknown",), issuer, fact,
            )

            def epoch(observed, receipt):
                # This fixture validates orchestration, not production effect settlement.
                assert observed == attempt
                assert receipt["setId"] == "coding-minimal"

            native_graph = AgentSession._prepare_resume_runtime_graph

            async def observe_graph(session, **kwargs):
                native_sessions.append(session)
                receipt = await native_graph(session, **kwargs)
                if mode in {"root_close", "cancel_prepare"}:
                    entered.set()
                    await asyncio.Event().wait()
                if mode == "cleanup_debt":
                    issuer.release_confirmation(fact)
                return receipt

            monkeypatch.setattr(AgentSession, "_prepare_resume_runtime_graph", observe_graph)
            if mode == "host_bind_failed":
                bind_host = AgentSession.set_extension_runtime_host

                def fail_host_binding(session, host):
                    bind_host(session, host)
                    if host is root:
                        raise OSError("original host binding failed")

                monkeypatch.setattr(AgentSession, "set_extension_runtime_host", fail_host_binding)
            if mode in {"cleanup_debt", "abort_failed"}:
                failures = []
                cleanup_method = "_dispose_after_session_shutdown" if mode == "abort_failed" else "dispose"
                native_cleanup = getattr(AgentSession, cleanup_method)

                async def fail_once(session, *args, **kwargs):
                    if not failures:
                        failures.append(session)
                        raise OSError("candidate cleanup failed")
                    await native_cleanup(session, *args, **kwargs)

                monkeypatch.setattr(AgentSession, cleanup_method, fail_once)
            operation = root.prepare_resume_continuation(
                session_file=path, plan=plan, current_owner_inputs=(), attempt=attempt,
                input_record_id="root-input-record", text="continue", no_tools=True,
                created_at=datetime(2026, 10, 12, tzinfo=UTC),
                require_current_admission=permission.require_current,
                require_current_epoch_settlement=epoch,
            )
            if mode in {"epoch_mismatch", "epoch_unselected", "epoch_fenced"}:
                if mode == "epoch_fenced":
                    selection.fence()
                expected = CodingResumeRecoveryRequired if mode == "epoch_mismatch" else RuntimeError
                with pytest.raises(expected, match="epoch"):
                    await operation
                assert path.read_bytes() == before
                assert not native_sessions
                assert not root._owned_transcript_factory.pending_preparations
                assert root.current_session is None
                return
            if mode in {"root_close", "cancel_prepare"}:
                task = asyncio.create_task(operation)
                waiter = asyncio.create_task(entered.wait())
                try:
                    await asyncio.wait((task, waiter), return_when=asyncio.FIRST_COMPLETED)
                    if not entered.is_set():
                        await task
                    if mode == "root_close":
                        await root.dispose_session_runtime()
                    else:
                        task.cancel()
                    with pytest.raises(asyncio.CancelledError):
                        await task
                finally:
                    waiter.cancel()
                    await asyncio.gather(waiter, return_exceptions=True)
                assert native_sessions[0].session_manager._lifecycle_session._disposed
            elif mode == "cleanup_debt":
                with pytest.raises(CodingResumeContinuationCleanupFailure) as failed:
                    await operation
                assert failed.value.original_owner is native_sessions[0]
                assert not native_sessions[0].session_manager._lifecycle_session._disposed
                assert root._resume_cleanup_debts == [failed.value]
                await root.dispose_session_runtime()
                assert native_sessions[0].session_manager._lifecycle_session._disposed
                assert not root._resume_cleanup_debts
            elif mode == "host_bind_failed":
                with pytest.raises(OSError, match="original host binding failed"):
                    await operation
                assert native_sessions[0].session_manager._lifecycle_session._disposed
                assert not root._resume_prepared_operations
            else:
                prepared = await operation
                candidate = prepared.continuation.session
                assert candidate is native_sessions[0]
                assert root.current_session is None
                assert not candidate._is_current_model_call_session()
                assert not prepared.consumed
                assert candidate.session_manager.header == header
                if mode in {"consume", "first_epoch_prepared", "delivered_close_failed"}:
                    result = await prepared.consume()
                    assert result.current is candidate
                    assert root.current_session is candidate
                    assert prepared.consumed
                    assert candidate._is_current_model_call_session()
                    assert not candidate.agent.is_streaming
                    if mode == "delivered_close_failed":
                        retire = AgentSession._dispose_after_session_shutdown
                        failures = []

                        async def fail_retirement_once(session):
                            if not failures:
                                failures.append(session)
                                raise OSError("delivered Session retirement failed")
                            await retire(session)

                        monkeypatch.setattr(AgentSession, "_dispose_after_session_shutdown", fail_retirement_once)
                        application_owners = tuple(selection._owners.values())
                        assert application_owners
                        close_product = selection.close
                        product_closes = []

                        def observe_product_close():
                            product_closes.append(True)
                            close_product()

                        monkeypatch.setattr(selection, "close", observe_product_close)
                        with pytest.raises(OSError, match="delivered Session retirement failed"):
                            await root.dispose_session_runtime()
                        assert not product_closes
                        assert not candidate.session_manager._lifecycle_session._disposed
                        for application_owner in application_owners:
                            application_owner.epoch_runtime.assert_current()
                        await root.dispose_session_runtime()
                        assert candidate.session_manager._lifecycle_session._disposed
                elif mode == "stale":
                    await root.new_session(cwd=str(tmp_path))
                    with pytest.raises(PreparedSessionOperationStateError):
                        await prepared.consume()
                    assert root.current_session is not candidate
                    assert candidate.session_manager._lifecycle_session._disposed
                elif mode == "delivery_revoked":
                    issuer.release_confirmation(fact)
                    with pytest.raises(PermissionError):
                        await prepared.consume()
                    assert root.current_session is None
                    assert candidate.session_manager._lifecycle_session._disposed
                elif mode == "cancel_delivery":
                    native_prepare_runtime = AgentSession.prepare_model_call_runtime

                    async def pause_delivery(session):
                        await native_prepare_runtime(session)
                        entered.set()
                        await asyncio.Event().wait()

                    monkeypatch.setattr(AgentSession, "prepare_model_call_runtime", pause_delivery)
                    task = asyncio.create_task(prepared.consume())
                    waiter = asyncio.create_task(entered.wait())
                    try:
                        await asyncio.wait((task, waiter), return_when=asyncio.FIRST_COMPLETED)
                        if not entered.is_set():
                            await task
                        await root.dispose_session_runtime()
                        with pytest.raises(asyncio.CancelledError):
                            await task
                    finally:
                        waiter.cancel()
                        await asyncio.gather(waiter, return_exceptions=True)
                    assert candidate.session_manager._lifecycle_session._disposed
                elif mode == "abort_failed":
                    with pytest.raises(OSError, match="candidate cleanup failed"):
                        await prepared.abort()
                    assert prepared._operation in root._resume_prepared_operations
                    assert not candidate.session_manager._lifecycle_session._disposed
                    await root.dispose_session_runtime()
                    assert candidate.session_manager._lifecycle_session._disposed
                else:
                    await prepared.abort()
                    assert candidate.session_manager._lifecycle_session._disposed
            _, records = load_agent_transcript_file(path, read_only=True)
            inputs = [record for record in records if record.record_id == "root-input-record"]
            assert len(inputs) == (0 if mode in {"root_close", "cancel_prepare", "cleanup_debt"} else 1)
        finally:
            if task is not None and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            await root.dispose_session_runtime()
            issuer.dispose()
        assert root.current_session is None
        assert not root._resume_activation_tasks
        assert not root._resume_delivery_tasks
        assert not root._resume_prepared_operations

    asyncio.run(scenario())
