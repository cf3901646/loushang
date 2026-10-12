from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime

import pytest

from loushang.ai.types import UserMessage
from loushang.coding.bootstrap import _create_resume_agent_session
from loushang.coding.composition_sets import resolve_coding_composition_set
from loushang.coding.resume_activation_attempt import (
    CodingActivationAttemptV1,
    CodingResumeRecoveryRequired,
    prepare_coding_activation_attempt_record,
)
from loushang.coding.resume_activation_plan import build_session_activation_plan
from loushang.coding.resume_binding import (
    CodingRuntimeBindingV1,
    coding_user_payload_digest,
)
from loushang.coding.resume_history import read_coding_resume_snapshot
from loushang.coding.session_manager import (
    SessionManager,
    _bind_owned_session_manager,
    _create_owned_session_factory,
)
from loushang.harness.conversation import StoreCommitOutcomeUnknown
from loushang.harness.session.bash import UserBashRequest
from loushang.harness.transcript.committer import PrebuiltUserMessageLookupResult

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux owned Coding Writer")


@pytest.mark.parametrize("mode", [
    "published", "input_unknown", "changed_leaf", "revoked", "unsettled",
    "receipt_changed", "graph_missing",
    "durable_lookup_unknown", "revoked_during_lookup",
    "durable_input_changed", "publication_cancelled",
])
def test_resume_publication_requires_exact_commit_current_graph_and_owner_checks(tmp_path, monkeypatch, mode):
    monkeypatch.setenv("LOUSHANG_HOME", str(tmp_path / "home"))

    async def scenario():
        original = await SessionManager.new(
            session_dir=tmp_path / "sessions", cwd=str(tmp_path), defer_materialization=False,
        )
        await original.append_message(UserMessage(role="user", content="history", timestamp=1.0))
        path = original.session_file
        header = original.header
        await original.dispose_runtime_profile()
        assert path is not None
        composition = resolve_coding_composition_set("coding-minimal")
        plan = build_session_activation_plan(
            read_coding_resume_snapshot(path, max_bytes=1024 * 1024), composition, workspace_root=tmp_path,
        )
        factory = _create_owned_session_factory()
        manager_type = _bind_owned_session_manager(factory)
        manager = await manager_type._load_resume_writer(path, plan=plan, current_owner_inputs=())
        attempt = CodingActivationAttemptV1(
            attempt_id="attempt-1", request_id="input-1", session_id=header.conversation_id,
            original_leaf_id=plan.selected_leaf_id, ancestry_digest=plan.ancestry_digest,
            plan_fingerprint=plan.plan_id, epoch_fingerprint="a" * 64, subject_digest="b" * 64,
        )
        revoked = False
        settlements = []
        session = None

        def admit(observed):
            assert observed == attempt
            if revoked:
                raise PermissionError("current subject revoked")

        def settle_epoch(observed, receipt):
            assert observed == attempt
            assert receipt["setId"] == "coding-minimal"
            settlements.append(observed.attempt_id)
            if mode == "unsettled":
                raise StoreCommitOutcomeUnknown("native effect is unsettled")

        try:
            await manager._commit_resume_activation_intent(prepare_coding_activation_attempt_record(
                attempt, created_at=datetime(2026, 10, 12, tzinfo=UTC),
            ))
            session = await _create_resume_agent_session(
                session_manager=manager, attempt_id=attempt.attempt_id,
                composition_set=composition, require_current_admission=admit, no_tools=True,
            )
            if mode != "graph_missing":
                await session._prepare_resume_runtime_graph(
                    attempt_id=attempt.attempt_id, require_current_admission=admit,
                )
            message = UserMessage(role="user", content="resume once", timestamp=2.0)

            def prepare_binding(persisted):
                return CodingRuntimeBindingV1(
                    attempt_id=attempt.attempt_id, input_id=attempt.request_id, record_id="record-1",
                    session_id=attempt.session_id, original_leaf_id=attempt.original_leaf_id,
                    ancestry_digest=attempt.ancestry_digest, subject_digest=attempt.subject_digest,
                    origin_composition=plan.composition_comparison.origin,
                    planned_fingerprint=attempt.plan_fingerprint, actual_fingerprint=attempt.epoch_fingerprint,
                    payload_digest=coding_user_payload_digest(persisted),
                )

            manager._stage_resume_first_user_input(
                message, prepare_binding=prepare_binding,
                created_at=datetime(2026, 10, 12, tzinfo=UTC),
                original_leaf_id=attempt.original_leaf_id, ancestry_digest=attempt.ancestry_digest,
                attempt_id=attempt.attempt_id,
            )
            if mode == "input_unknown":
                store = manager._lifecycle_session.runtime_binding.store
                append = store.append

                async def lose_ack(*args, **kwargs):
                    await append(*args, **kwargs)
                    raise StoreCommitOutcomeUnknown("input acknowledgement lost")

                monkeypatch.setattr(store, "append", lose_ack)
                with pytest.raises(StoreCommitOutcomeUnknown):
                    await manager.append_message(message)
            else:
                assert await manager.append_message(message) == "record-1"
            assert manager.resume_runtime_publication_pending
            assert not session.execution_available
            before = path.read_bytes()
            if mode == "durable_input_changed":
                changed = before.replace(b"resume once", b"broken once")
                assert changed != before
                path.write_bytes(changed)
                before = changed
            if mode == "changed_leaf":
                manager.branch(attempt.original_leaf_id)
            if mode == "revoked":
                revoked = True
            if mode in {"durable_lookup_unknown", "revoked_during_lookup"}:
                lookup = manager.lookup_prebuilt_user_message

                async def observe_input(record):
                    nonlocal revoked
                    result = await lookup(record)
                    if mode == "revoked_during_lookup":
                        revoked = True
                        return result
                    return PrebuiltUserMessageLookupResult(record.record_id, "unknown")

                monkeypatch.setattr(manager, "lookup_prebuilt_user_message", observe_input)
            if mode == "receipt_changed":
                build = session._build_current_coding_composition_receipt

                def changed_receipt():
                    receipt = build()
                    receipt["catalogSelectionFingerprint"] = "c" * 64
                    return receipt

                monkeypatch.setattr(session, "_build_current_coding_composition_receipt", changed_receipt)
            if mode == "publication_cancelled":
                entered, release = asyncio.Event(), asyncio.Event()
                lookup = manager.lookup_prebuilt_user_message

                async def held_lookup(record):
                    entered.set()
                    await release.wait()
                    return await lookup(record)

                monkeypatch.setattr(manager, "lookup_prebuilt_user_message", held_lookup)
                task = asyncio.create_task(session._publish_resume_runtime(
                    attempt_id=attempt.attempt_id, input_record_id="record-1",
                    require_current_admission=admit, require_current_epoch_settlement=settle_epoch,
                ))
                waiting = asyncio.create_task(entered.wait())
                try:
                    await asyncio.wait((task, waiting), return_when=asyncio.FIRST_COMPLETED)
                    if not entered.is_set():
                        await task
                        pytest.fail("publication returned before its durable lookup")
                    assert task.cancel()
                    with pytest.raises(asyncio.CancelledError):
                        await task
                finally:
                    release.set()
                    waiting.cancel()
                    if not task.done():
                        task.cancel()
                    await asyncio.gather(task, waiting, return_exceptions=True)
                assert not session.execution_available
                assert manager.resume_runtime_publication_pending
                assert not settlements
                assert path.read_bytes() == before
            elif mode == "published":
                await session._publish_resume_runtime(
                    attempt_id=attempt.attempt_id, input_record_id="record-1",
                    require_current_admission=admit, require_current_epoch_settlement=settle_epoch,
                )
                assert settlements
                assert session.execution_available
                assert not manager.resume_runtime_publication_pending
                await session.prepare_model_call_runtime()
                assert manager.header == header
                assert path.read_bytes() == before
                await manager.append_message(UserMessage(role="user", content="next", timestamp=3.0))
                await session.prepare_model_call_runtime()
                revoked = True
                with pytest.raises(PermissionError):
                    await session.prepare_model_call_runtime()
                with pytest.raises(PermissionError):
                    await session.compact()
                with pytest.raises(PermissionError):
                    await session._before_bash(UserBashRequest("blocked", str(tmp_path), False))
                with pytest.raises(PermissionError):
                    await session._exec_command_from_extension("blocked")
                revoked = False
                manager.branch(attempt.original_leaf_id)
                with pytest.raises(CodingResumeRecoveryRequired):
                    await session.prepare_model_call_runtime()
            else:
                expected = (
                    PermissionError if mode in {"revoked", "revoked_during_lookup"} else StoreCommitOutcomeUnknown
                    if mode == "unsettled" else CodingResumeRecoveryRequired
                )
                with pytest.raises(expected):
                    await session._publish_resume_runtime(
                        attempt_id=attempt.attempt_id, input_record_id="record-1",
                        require_current_admission=admit, require_current_epoch_settlement=settle_epoch,
                    )
                assert not session.execution_available
                assert manager.resume_runtime_publication_pending
                assert path.read_bytes() == before
                if mode not in {"unsettled"}:
                    assert not settlements
        finally:
            if session is not None:
                await session.dispose()
            else:
                await manager.dispose_runtime_profile()
            await factory.close()

    asyncio.run(scenario())
