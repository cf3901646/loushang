from __future__ import annotations

import asyncio
import hashlib
import sys
from datetime import UTC, datetime

import pytest

from loushang.ai.api_registry import get_default_api_registry
from loushang.ai.json_codec import serialize_message
from loushang.ai.model import Auth, Capabilities, Model
from loushang.ai.prepared_request import PreparedModelRequest
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
from loushang.coding.resume_history import read_coding_resume_snapshot
from loushang.coding.resume_input_lookup import coding_resume_input_record_digest
from loushang.coding.resume_model_outcome import observe_coding_resume_model_outcome
from loushang.coding.resume_permission_confirmation import (
    CodingResumePermissionConfirmation,
    coding_resume_permission_request,
)
from loushang.coding.runtime.agent_session_runtime import AgentSessionRuntime
from loushang.coding.session_manager import SessionManager
from loushang.harness.approval import DenyApprovalResolver, InteractiveApprovalResolver
from loushang.harness.session.request_evidence import RESOURCE_EVIDENCE_METADATA_KEY
from loushang.harness.transcript.jsonl_file import load_agent_transcript_file

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux owned Resume Writer")


@pytest.mark.parametrize("mode", ["completed", "skill_changed", "agents_changed", "revoked", "revoked_at_barrier", "unknown_transport", "cancelled", "slot_replaced", "root_closed"])
def test_root_first_input_uses_native_model_transport_once(tmp_path, monkeypatch, mode):
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
        composition_id = "coding-standard" if mode in {"skill_changed", "agents_changed"} else "coding-minimal"
        context_file = tmp_path / "AGENTS.md"
        if mode == "agents_changed":
            context_file.write_text("OLD workspace instruction.\n")
        skill = tmp_path / "skills" / "review" / "SKILL.md"
        if mode == "skill_changed":
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: review\ndescription: Review\n---\nOLD review instruction.\n")
        model = Model(
            id="root-test", name="Root Test", provider="faux", endpoint="root-resume",
            api="root-resume-test", base_url="https://provider.test/v1", auth=Auth(kind="none"),
            capabilities=Capabilities(input=("text",), output=("text",), stream=True,
                                      context_window=128000, max_tokens=4096),
        )
        selection = CodingFencedProductApplicationSelection()

        def ordinary_factory(manager, **kwargs):
            return bootstrap.create_agent_session(
                session_manager=manager, composition_set=composition_id, no_tools=True,
                model=model, package_product_runtime_factory=selection.factory_for_session(manager),
                **kwargs,
            )

        root = AgentSessionRuntime(
            session_dir=tmp_path / "sessions", session_factory=ordinary_factory,
            owned_transcripts=True, product_owner_selection=selection,
        )
        issuer = InteractiveApprovalResolver(fallback=DenyApprovalResolver())
        registry = get_default_api_registry()
        requests = []
        entered, release = asyncio.Event(), asyncio.Event()
        task = None

        class Adapter:
            api = "root-resume-test"

            def prepare_request(self, request):
                return PreparedModelRequest.from_provider_request(request, payload={
                    "messages": [serialize_message(message) for message in request.context.messages],
                    "model": request.model.id,
                })

            async def invoke_prepared_raw(self, request, prepared):
                prepared.payload_for_transport()
                assert request.attempt == 1
                requests.append(request.context)
                entered.set()
                if mode == "cancelled":
                    await release.wait()
                if mode == "unknown_transport":
                    raise ConnectionError("provider outcome unknown")
                yield {"type": "response_start", "response_id": "root-response"}
                yield {"type": "text_delta", "text": "reply"}
                yield {"type": "stop_reason", "stop_reason": "stop"}
                yield {"type": "response_done"}

            async def invoke_raw(self, request):
                pytest.fail("original prepared transport was bypassed")
                yield {}

        registry.register_api_adapter(Adapter(), source_id="root-resume-test")
        try:
            history = await root.preview_resume_history(path)
            plan = build_session_activation_plan(
                history, resolve_coding_composition_set(composition_id), workspace_root=tmp_path,
            )
            if mode == "skill_changed":
                skill.write_text("---\nname: review\ndescription: Review\n---\nReview CURRENT source bytes.\n")
            elif mode == "agents_changed":
                context_file.write_text("Use CURRENT workspace instruction.\n")
            attempt = CodingActivationAttemptV1(
                attempt_id="root-attempt", request_id="root-input", session_id=header.conversation_id,
                original_leaf_id=plan.selected_leaf_id, ancestry_digest=plan.ancestry_digest,
                plan_fingerprint=plan.plan_id, epoch_fingerprint="a" * 64, subject_digest="b" * 64,
            )

            async def confirm(payload):
                assert await issuer.handle_result(payload["action_id"], outcome="allow_once")

            issuer.set_request_presenter(confirm)
            fact = await issuer.confirm(coding_resume_permission_request(
                attempt, actor_id="root", expansion_codes=("authority.unknown",),
            ))
            assert fact is not None
            permission = CodingResumePermissionConfirmation(attempt, "root", ("authority.unknown",), issuer, fact)

            def epoch(observed, receipt):
                # Production external effect settlement remains a separate owner gate.
                assert observed == attempt
                assert receipt["setId"] == composition_id

            prepared = await root.prepare_resume_continuation(
                session_file=path, plan=plan, current_owner_inputs=(), attempt=attempt,
                input_record_id="root-input-record", model=model, no_tools=True,
                text="/skill:review continue once" if mode == "skill_changed" else "continue once",
                created_at=datetime(2026, 10, 12, tzinfo=UTC),
                require_current_admission=permission.require_current,
                require_current_epoch_settlement=epoch,
            )
            candidate = prepared.continuation.session
            committed = path.read_bytes()
            with pytest.raises(CodingResumeRecoveryRequired, match="model.root_not_delivered"):
                await prepared.run_first_input()
            assert path.read_bytes() == committed
            assert not requests
            assert not candidate._coding_resume_dispatch_claimed
            await prepared.consume()
            assert root.current_session is candidate
            if mode == "revoked":
                issuer.release_confirmation(fact)
            elif mode == "root_closed":
                await root.dispose_session_runtime()
            elif mode == "slot_replaced":
                await root.new_session(cwd=str(tmp_path))
            elif mode == "revoked_at_barrier":
                transcript = candidate.session_manager._transcript
                append_snapshot = transcript.append_model_input_snapshot

                async def revoke_after_snapshot(*args, **kwargs):
                    result = await append_snapshot(*args, **kwargs)
                    issuer.release_confirmation(fact)
                    return result

                monkeypatch.setattr(transcript, "append_model_input_snapshot", revoke_after_snapshot)
            if mode == "revoked":
                with pytest.raises(PermissionError):
                    await prepared.run_first_input()
            elif mode in {"root_closed", "slot_replaced"}:
                with pytest.raises(CodingResumeRecoveryRequired):
                    await prepared.run_first_input()
            elif mode == "cancelled":
                task = asyncio.create_task(prepared.run_first_input())
                waiter = asyncio.create_task(entered.wait())
                try:
                    await asyncio.wait((task, waiter), return_when=asyncio.FIRST_COMPLETED)
                    if not entered.is_set():
                        await task
                    task.cancel()
                    release.set()
                    with pytest.raises(asyncio.CancelledError):
                        await task
                finally:
                    waiter.cancel()
                    release.set()
                    await asyncio.gather(waiter, return_exceptions=True)
            else:
                await prepared.run_first_input()
            saved = path.read_bytes()
            if mode in {"completed", "skill_changed", "agents_changed", "unknown_transport", "cancelled", "revoked_at_barrier"}:
                with pytest.raises(CodingResumeRecoveryRequired, match="model.dispatch_already_claimed"):
                    await prepared.run_first_input()
                assert path.read_bytes() == saved
            durable_header, records = load_agent_transcript_file(path, read_only=True)
            assert durable_header == header
            assert len([record for record in records if isinstance(record.payload, UserMessage)]) == 2
            committed_input = next(record for record in records if record.record_id == "root-input-record")
            assert coding_resume_input_record_digest(committed_input) == prepared.continuation.input_lookup_query.record_digest
            expected_calls = int(mode in {"completed", "skill_changed", "agents_changed", "unknown_transport", "cancelled"})
            assert len(requests) == expected_calls
            if requests:
                user_inputs = [serialize_message(message) for message in requests[0].messages if getattr(message, "role", None) == "user"]
                if mode == "skill_changed":
                    assert len(user_inputs) == 2
                    assert user_inputs[0]["content"][0]["text"] == "history"
                    assert "Review CURRENT source bytes." in user_inputs[1]["content"][0]["text"]
                    assert "OLD review instruction." not in user_inputs[1]["content"][0]["text"]
                    evidence = committed_input.metadata[RESOURCE_EVIDENCE_METADATA_KEY]
                    assert evidence["skills"][0]["observedContentDigest"] == hashlib.sha256(skill.read_bytes()).hexdigest()
                else:
                    assert [message["content"][0]["text"] for message in user_inputs] == ["history", "continue once"]
                    if mode == "agents_changed":
                        assert "Use CURRENT workspace instruction." in requests[0].system_prompt
                        assert "OLD workspace instruction." not in requests[0].system_prompt
            snapshots = [record for record in records if record.kind == "model.input.prepared"]
            assert len(snapshots) == int(mode in {"completed", "skill_changed", "agents_changed", "unknown_transport", "cancelled", "revoked_at_barrier"})
            outcome = observe_coding_resume_model_outcome(
                read_coding_resume_snapshot(path, max_bytes=1024 * 1024),
                prepared.continuation.input_lookup_query,
            )
            assert outcome.status == {
                "completed": "observed_completed", "skill_changed": "observed_completed", "agents_changed": "observed_completed", "unknown_transport": "observed_failed",
                "cancelled": "observed_cancelled",
            }.get(mode, "unknown")
        finally:
            release.set()
            if task is not None and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            await root.dispose_session_runtime()
            issuer.dispose()
            registry.unregister_api_adapters("root-resume-test")

    asyncio.run(scenario())
