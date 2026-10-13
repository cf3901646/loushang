from __future__ import annotations

import asyncio
import hashlib
import sys
from datetime import UTC, datetime

import pytest

from loushang.ai.types import UserMessage
from loushang.coding import bootstrap
from loushang.coding.composition_sets import resolve_coding_composition_set
from loushang.coding.embedded_resume import (
    EmbeddedResumeApprovalInteraction,
    EmbeddedResumeInputCoordinator,
)
from loushang.coding.package_product_runtime import (
    CodingFencedProductApplicationSelection,
)
from loushang.coding.resume_activation_attempt_v2 import CodingActivationAttemptV2
from loushang.coding.resume_activation_plan import build_session_activation_plan
from loushang.coding.runtime.agent_session_runtime import AgentSessionRuntime
from loushang.coding.session_manager import SessionManager
from loushang.harness.approval import DenyApprovalResolver, InteractiveApprovalResolver
from loushang.harness.config.agent import SettingsManager
from loushang.harness.tools.workspace.factory import workspace_tool_runtime_settings
from loushang.harnesstui.conversation.control import ConversationTextAction

pytestmark = pytest.mark.skipif(
    sys.platform != "linux", reason="Linux owned Resume Root"
)


@pytest.mark.parametrize(
    ("composition_id", "no_tools", "expected_owners"),
    [
        ("coding-minimal", None, ()),
        (
            "coding-standard",
            None,
            ("harness.plugin-activation", "harness.plugin-execution"),
        ),
        ("coding-standard", True, ()),
    ],
)
def test_embedded_coordinator_prepares_exact_v2_input_from_current_root(
    tmp_path,
    monkeypatch,
    composition_id,
    no_tools,
    expected_owners,
):
    monkeypatch.setenv("LOUSHANG_HOME", str(tmp_path / "home"))

    async def scenario():
        manager = await SessionManager.new(
            session_dir=tmp_path / "sessions",
            cwd=str(tmp_path),
            defer_materialization=False,
        )
        await manager.append_message(
            UserMessage(role="user", content="history", timestamp=1.0)
        )
        path = manager.session_file
        assert path is not None
        await manager.dispose_runtime_profile()

        settings = SettingsManager(
            global_settings_path=tmp_path / "user.json",
            project_settings_path=tmp_path / "project.json",
        )
        services = bootstrap.create_services(settings_manager=settings)
        policy = workspace_tool_runtime_settings(settings).policy_engine
        selection = CodingFencedProductApplicationSelection()
        root = AgentSessionRuntime(
            session_dir=tmp_path / "sessions",
            session_factory=lambda *_args, **_kwargs: None,  # unused by this gate
            owned_transcripts=True,
            product_owner_selection=selection,
        )
        approval = InteractiveApprovalResolver(fallback=DenyApprovalResolver())
        root._bind_embedded_resume_approval_owner(approval)
        history = await root.preview_resume_history(path)
        plan = build_session_activation_plan(
            history,
            resolve_coding_composition_set(composition_id),
            workspace_root=tmp_path,
        )
        captured = {}

        async def prepare_plan(observed):
            assert observed is history
            return plan

        async def prepare_continuation(**kwargs):
            captured.update(kwargs)
            return "prepared"

        monkeypatch.setattr(root, "prepare_configured_resume_plan", prepare_plan)
        monkeypatch.setattr(
            root,
            "prepare_embedded_resume_epoch",
            lambda workspace, **_kwargs: "e" * 64,
        )
        monkeypatch.setattr(
            root, "prepare_resume_continuation", prepare_continuation
        )

        interaction = EmbeddedResumeApprovalInteraction(approval, settings)

        async def confirm(payload):
            assert root.current_session is None
            assert await interaction.respond(
                payload["action_id"], outcome="allow_once"
            )

        presentation = interaction.bind_presenter(confirm)
        ids = iter(("a", "b", "c"))
        coordinator = EmbeddedResumeInputCoordinator(
            runtime=root,
            services=services,
            policy_evaluator=policy,
            no_tools=no_tools,
            now=lambda: datetime(2026, 10, 13, tzinfo=UTC),
            id_factory=lambda: next(ids),
        )
        try:
            with root.resume_history_view_scope(path, history):
                result = await coordinator.prepare_input(
                    session_file=path,
                    history=history,
                    action=ConversationTextAction("continue"),
                    observe_input_identity=lambda _query: None,
                )
            assert result == "prepared"
            attempt = captured["attempt"]
            assert type(attempt) is CodingActivationAttemptV2
            assert attempt.attempt_id == "resume-attempt:a"
            assert attempt.request_id == "resume-input:b"
            assert captured["input_record_id"] == "resume-record:c"
            assert tuple(owner.owner_id for owner in attempt.effect_owners) == (
                expected_owners
            )
            assert captured["current_owner_inputs"] == plan.owner_inputs
            assert captured["approval_resolver"] is approval
            assert captured["tool_policy_evaluator"] is policy
            state_id = hashlib.sha256(
                b"loushang.coding-capability-plugin-state/v1\0"
                + plan.session_id.encode()
            ).hexdigest()
            assert not (
                tmp_path
                / "sessions"
                / "plugin-state"
                / "coding-capability-plugins"
                / state_id
            ).exists()
            captured["require_current_admission"](attempt)
            if not expected_owners:
                captured["require_current_epoch_settlement"](
                    attempt,
                    {"setId": composition_id, "selectedRevisions": []},
                )
        finally:
            presentation.close()
            await root.dispose_session_runtime()
            approval.dispose()

    asyncio.run(scenario())


def test_embedded_coordinator_refuses_worker_without_c5_settlement(tmp_path):
    settings = SettingsManager(
        global_settings_path=tmp_path / "user.json",
        project_settings_path=tmp_path / "project.json",
    )
    services = bootstrap.create_services(settings_manager=settings)
    selection = CodingFencedProductApplicationSelection(worker_candidates=True)
    root = AgentSessionRuntime(
        session_dir=tmp_path / "sessions",
        session_factory=lambda *_args, **_kwargs: None,
        owned_transcripts=True,
        product_owner_selection=selection,
    )
    with pytest.raises(Exception, match="effect_owner_set_unsupported"):
        EmbeddedResumeInputCoordinator(
            runtime=root,
            services=services,
            policy_evaluator=workspace_tool_runtime_settings(settings).policy_engine,
            worker_candidate_plugin_id="worker.example",
        )
