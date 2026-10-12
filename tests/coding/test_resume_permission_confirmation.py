from __future__ import annotations

import asyncio
from dataclasses import replace

import pytest

from loushang.coding.resume_activation_attempt import CodingActivationAttemptV1
from loushang.coding.resume_permission_confirmation import (
    CodingResumePermissionConfirmation,
    coding_resume_permission_request,
)
from loushang.harness.approval import DenyApprovalResolver, InteractiveApprovalResolver
from loushang.harness.authorization import EffectiveExecutionProfile
from loushang.harness.config.agent import SettingsManager
from loushang.harness.tools.workspace.factory import workspace_tool_runtime_settings


@pytest.mark.parametrize("mode", ["current", "profile", "managed_rules", "await_change", "missing_policy"])
def test_resume_confirmation_revalidates_native_current_policy(tmp_path, mode):
    async def scenario():
        settings = SettingsManager(
            global_settings_path=tmp_path / "user.json", project_settings_path=tmp_path / "project.json",
        )
        policy = workspace_tool_runtime_settings(settings).policy_engine
        attempt = CodingActivationAttemptV1(
            attempt_id="attempt-1", request_id="input-1", session_id="session-1",
            original_leaf_id="leaf-1", ancestry_digest="a" * 64,
            plan_fingerprint="b" * 64, epoch_fingerprint="c" * 64, subject_digest="d" * 64,
        )
        owner = InteractiveApprovalResolver(fallback=DenyApprovalResolver())

        async def present(payload):
            assert len(payload["arguments"]["policyConfigurationFingerprint"]) == 64
            if mode == "await_change":
                settings.set_permission_profile("full_access", scope="session")
            assert await owner.handle_result(payload["action_id"], outcome="allow_once")

        owner.set_request_presenter(present)
        try:
            fact = await owner.confirm(coding_resume_permission_request(
                attempt, actor_id="root", expansion_codes=("authority.unknown",), policy_evaluator=policy,
            ))
            assert fact is not None
            bound = CodingResumePermissionConfirmation(
                attempt, "root", ("authority.unknown",), owner, fact, policy_evaluator=policy,
            )
            if mode == "profile":
                settings.set_permission_profile("full_access", scope="session")
            elif mode == "managed_rules":
                settings.update_settings(scope="session", tools={"blocked_tools": ["bash"]})
            fresh = workspace_tool_runtime_settings(settings).policy_engine
            if mode == "missing_policy":
                fresh = None
            if mode == "current":
                bound.require_current(attempt, current_policy_evaluator=fresh)
            else:
                with pytest.raises(PermissionError):
                    bound.require_current(attempt, current_policy_evaluator=fresh)
        finally:
            owner.dispose()

    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["current", "read", "write", "network", "denial", "missing_scope", "current_scope_changed"])
def test_native_resume_confirmation_binds_execution_scope(tmp_path, mode):
    async def scenario():
        attempt = CodingActivationAttemptV1(
            attempt_id="attempt-1", request_id="input-1", session_id="session-1",
            original_leaf_id="leaf-1", ancestry_digest="a" * 64,
            plan_fingerprint="b" * 64, epoch_fingerprint="c" * 64, subject_digest="d" * 64,
        )
        profile = EffectiveExecutionProfile(
            readable_roots=(tmp_path,), writable_roots=(tmp_path / "output",),
            denied_roots=(tmp_path / "secret",), network="restricted",
        )
        expansion = ("authority.unknown",)
        owner = InteractiveApprovalResolver(fallback=DenyApprovalResolver())

        async def present(payload):
            assert payload["arguments"]["permissionExpansion"] == [
                "authority.unknown", "execution.baseline_unknown",
            ]
            assert payload["arguments"]["executionScope"]["network"] == "restricted"
            assert payload["arguments"]["executionScope"]["writableRoots"] == [str(tmp_path / "output")]
            assert await owner.handle_result(payload["action_id"], outcome="allow_once")

        owner.set_request_presenter(present)
        try:
            fact = await owner.confirm(coding_resume_permission_request(
                attempt, actor_id="root", expansion_codes=expansion, execution_profile=profile,
            ))
            assert fact is not None
            bound = CodingResumePermissionConfirmation(
                attempt, "root", expansion, owner, fact, execution_profile=profile,
            )
            bound.require_current(attempt, current_execution_profile=profile)
            observed = profile
            if mode == "current":
                owner.release_confirmation(fact)
            elif mode == "missing_scope":
                observed = None
            elif mode == "current_scope_changed":
                observed = replace(profile, network="allowed")
            else:
                changed = replace(profile, **{
                    "read": {"readable_roots": (tmp_path.parent,)},
                    "write": {"writable_roots": (tmp_path,)},
                    "network": {"network": "allowed"},
                    "denial": {"denied_roots": ()},
                }[mode])
                bound = replace(bound, execution_profile=changed)
                observed = changed
            with pytest.raises(PermissionError):
                bound.require_current(attempt, current_execution_profile=observed)
        finally:
            owner.dispose()

    asyncio.run(scenario())


def test_resume_execution_scope_request_rejects_unbounded_scope_bytes(tmp_path):
    attempt = CodingActivationAttemptV1(
        attempt_id="attempt-1", request_id="input-1", session_id="session-1",
        original_leaf_id="leaf-1", ancestry_digest="a" * 64,
        plan_fingerprint="b" * 64, epoch_fingerprint="c" * 64, subject_digest="d" * 64,
    )
    root = tmp_path
    for _ in range(6):
        root /= "x" * 100
    profile = EffectiveExecutionProfile(readable_roots=tuple(root / str(index) for index in range(64)))
    with pytest.raises(ValueError, match="byte budget"):
        coding_resume_permission_request(
            attempt, actor_id="root", expansion_codes=("authority.unknown",), execution_profile=profile,
        )


@pytest.mark.parametrize("mode", [
    "current", "actor", "scope", "subject", "candidate", "plan", "leaf", "session", "ancestry",
])
def test_permission_confirmation_is_bound_to_current_native_action(mode):
    async def scenario():
        attempt = CodingActivationAttemptV1(
            attempt_id="attempt-1", request_id="input-1", session_id="session-1",
            original_leaf_id="leaf-1", ancestry_digest="a" * 64,
            plan_fingerprint="b" * 64, epoch_fingerprint="c" * 64, subject_digest="d" * 64,
        )
        owner = InteractiveApprovalResolver(fallback=DenyApprovalResolver())
        expansion = ("authority.unknown", "workspace.write")
        native_request = coding_resume_permission_request(attempt, actor_id="actor-1", expansion_codes=expansion)

        async def present(payload):
            assert payload["policy_code"] == "resume_permission_expansion"
            assert payload["arguments"]["permissionExpansion"] == list(expansion)
            assert await owner.handle_result(payload["action_id"], outcome="allow_once")

        owner.set_request_presenter(present)
        try:
            fact = await owner.confirm(native_request)
            assert fact is not None
            bound = CodingResumePermissionConfirmation(attempt, "actor-1", expansion, owner, fact)
            bound.require_current(attempt)
            if mode == "actor":
                bound = replace(bound, actor_id="actor-2")
            elif mode == "scope":
                bound = replace(bound, expansion_codes=("full_access",))
            elif mode != "current":
                field, value = {
                    "subject": ("subject_digest", "e" * 64),
                    "candidate": ("epoch_fingerprint", "e" * 64),
                    "plan": ("plan_fingerprint", "e" * 64),
                    "leaf": ("original_leaf_id", "leaf-2"),
                    "session": ("session_id", "session-2"),
                    "ancestry": ("ancestry_digest", "e" * 64),
                }[mode]
                attempt = replace(attempt, **{field: value})
                # Even rebinding the data wrapper cannot widen the native fact.
                bound = replace(bound, attempt=attempt)
            if mode != "current":
                with pytest.raises(PermissionError):
                    bound.require_current(attempt)
            else:
                owner.release_confirmation(fact)
                with pytest.raises(PermissionError):
                    bound.require_current(attempt)
        finally:
            owner.dispose()

    asyncio.run(scenario())
