from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from loushang.harness.config.agent import SettingsManager
from loushang.harness.permissions import (
    PermissionProfileCeiling,
    PermissionProfilePolicyEvaluator,
    permission_profile_snapshot,
)
from loushang.harness.policy import (
    PolicyDecision,
    ToolPolicySubject,
)
from loushang.harness.policy.engine import PolicyEngine
from loushang.harness.tools.workspace.factory import workspace_tool_runtime_settings


def test_native_policy_fingerprint_reads_current_settings_inputs(tmp_path):
    settings = SettingsManager(
        global_settings_path=tmp_path / "user.json", project_settings_path=tmp_path / "project.json",
    )
    policy = workspace_tool_runtime_settings(settings).policy_engine
    assert isinstance(policy, PermissionProfilePolicyEvaluator)
    initial = policy.configuration_fingerprint()
    assert len(initial) == 64
    assert workspace_tool_runtime_settings(settings).policy_engine.configuration_fingerprint() == initial
    settings.set_permission_profile("full_access", scope="session")
    assert policy.configuration_fingerprint() != initial
    settings.set_permission_profile("standard", scope="session")
    assert policy.configuration_fingerprint() == initial
    settings.update_settings(scope="session", tools={"blocked_tools": ["bash"]})
    fresh = workspace_tool_runtime_settings(settings).policy_engine
    assert fresh.configuration_fingerprint() != initial
    assert policy.configuration_fingerprint() == fresh.configuration_fingerprint()
    assert asyncio.run(policy.evaluate(ToolPolicySubject(tool_name="bash", arguments={}))).disposition == "deny"


def test_policy_fingerprint_preserves_managed_rule_inputs():
    first = PolicyEngine(blocked_tools=("bash",))
    assert first.configuration_fingerprint() == PolicyEngine(blocked_tools=("bash",)).configuration_fingerprint()
    assert first.configuration_fingerprint() != PolicyEngine(ask_tools=("bash",)).configuration_fingerprint()


@dataclass(frozen=True)
class _Policy:
    decision: PolicyDecision

    def evaluate(self, subject: object) -> PolicyDecision:
        del subject
        return self.decision


def _evaluate(
    *,
    profile: str,
    decision: PolicyDecision,
    tool_name: str = "bash",
    ceiling: PermissionProfileCeiling | None = None,
) -> PolicyDecision:
    evaluator = PermissionProfilePolicyEvaluator(
        _Policy(decision),
        profile_provider=lambda: profile,  # type: ignore[arg-type]
        ceiling_provider=lambda: ceiling or PermissionProfileCeiling(),
    )
    return asyncio.run(
        evaluator.evaluate(
            ToolPolicySubject(tool_name=tool_name, arguments={})
        )
    )


def test_permission_profile_snapshot_applies_the_managed_ceiling() -> None:
    snapshot = permission_profile_snapshot(
        "full_access",
        PermissionProfileCeiling(
            maximum_profile="standard",
            reason="Managed environment limits this session.",
        ),
    )

    assert snapshot.requested_profile_id == "full_access"
    assert snapshot.effective_profile.profile_id == "standard"
    full_access = next(
        option
        for option in snapshot.options
        if option.profile.profile_id == "full_access"
    )
    assert full_access.enabled is False
    assert full_access.disabled_reason == "Managed environment limits this session."


def test_standard_profile_preserves_policy_decisions() -> None:
    ask = PolicyDecision.ask("Publish refs", code="git_publish")

    assert _evaluate(profile="standard", decision=ask) == ask


def test_full_access_skips_optional_approval_but_never_managed_deny() -> None:
    assert _evaluate(
        profile="full_access",
        decision=PolicyDecision.ask("Delete files", code="delete"),
    ) == PolicyDecision(disposition="allow", code="delete")

    deny = PolicyDecision.deny("Managed deny", code="managed_deny")
    assert _evaluate(profile="full_access", decision=deny) == deny


def test_managed_ceiling_makes_a_full_access_request_effectively_standard() -> None:
    ask = PolicyDecision.ask("Publish refs", code="git_publish")

    assert _evaluate(
        profile="full_access",
        decision=ask,
        ceiling=PermissionProfileCeiling(maximum_profile="standard"),
    ) == ask


@pytest.mark.parametrize("tool_name", ["write", "edit"])
def test_cautious_profile_asks_before_direct_workspace_mutations(
    tool_name: str,
) -> None:
    decision = _evaluate(
        profile="cautious",
        decision=PolicyDecision.allow(),
        tool_name=tool_name,
    )

    assert decision.disposition == "ask"
    assert decision.code == "cautious_workspace_mutation"


def test_cautious_profile_does_not_add_prompts_to_read_only_tools() -> None:
    assert _evaluate(
        profile="cautious",
        decision=PolicyDecision.allow(),
        tool_name="read",
    ) == PolicyDecision.allow()
