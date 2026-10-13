from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime

import pytest

from loushang.ai.types import UserMessage
from loushang.coding.composition_sets import resolve_coding_composition_set
from loushang.coding.resume_activation_attempt import CodingResumeRecoveryRequired
from loushang.coding.resume_activation_attempt_v2 import CodingActivationAttemptV2
from loushang.coding.resume_activation_plan import build_session_activation_plan
from loushang.coding.resume_continuation import prepare_coding_resume_continuation
from loushang.coding.resume_history import read_coding_resume_snapshot
from loushang.coding.session_manager import (
    SessionManager,
    _bind_owned_session_manager,
    _create_owned_session_factory,
)

pytestmark = pytest.mark.skipif(
    sys.platform != "linux", reason="Linux owned Resume Writer"
)


@pytest.mark.parametrize("partial_tail", [False, True])
def test_v1_continuation_refuses_v2_before_admission_writer_or_tail_repair(
    tmp_path, monkeypatch, partial_tail
):
    monkeypatch.setenv("LOUSHANG_HOME", str(tmp_path / "home"))

    async def scenario():
        original = await SessionManager.new(
            session_dir=tmp_path / "sessions",
            cwd=str(tmp_path),
            defer_materialization=False,
        )
        await original.append_message(
            UserMessage(role="user", content="history", timestamp=1.0)
        )
        path = original.session_file
        await original.dispose_runtime_profile()
        assert path is not None
        history = read_coding_resume_snapshot(path, max_bytes=1024 * 1024)
        plan = build_session_activation_plan(
            history,
            resolve_coding_composition_set("coding-standard"),
            workspace_root=tmp_path,
        )
        attempt = CodingActivationAttemptV2(
            attempt_id="attempt-2",
            request_id="input-2",
            session_id=plan.session_id,
            original_leaf_id=plan.selected_leaf_id,
            ancestry_digest=plan.ancestry_digest,
            plan_fingerprint=plan.plan_id,
            epoch_fingerprint="a" * 64,
            subject_digest="b" * 64,
        )
        if partial_tail:
            with path.open("ab") as stream:
                stream.write(b'{"recordId":"future-uncommitted",')
        before = {
            item.relative_to(tmp_path): item.read_bytes()
            for item in tmp_path.rglob("*")
            if item.is_file()
        }
        factory = _create_owned_session_factory()
        manager_type = _bind_owned_session_manager(factory)

        def reject(*args, **kwargs):
            pytest.fail(
                "unsupported protocol must refuse before current owner callbacks"
            )

        async def reject_writer(*args, **kwargs):
            pytest.fail(
                "unsupported protocol must refuse before original Writer acquisition"
            )

        monkeypatch.setattr(
            manager_type, "_load_resume_writer", classmethod(reject_writer)
        )
        try:
            with pytest.raises(CodingResumeRecoveryRequired) as caught:
                await prepare_coding_resume_continuation(
                    manager_type=manager_type,
                    session_file=path,
                    plan=plan,
                    current_owner_inputs=(),
                    attempt=attempt,
                    input_record_id="message-2",
                    text="continue",
                    created_at=datetime(2026, 10, 13, tzinfo=UTC),
                    require_current_admission=reject,
                    require_current_epoch_settlement=reject,
                )
            assert caught.value.reason_code == "writer.resume_protocol_unsupported"
            assert factory.pending_preparations == ()
            after = {
                item.relative_to(tmp_path): item.read_bytes()
                for item in tmp_path.rglob("*")
                if item.is_file()
            }
            assert after == before
        finally:
            await factory.close()

    asyncio.run(scenario())
