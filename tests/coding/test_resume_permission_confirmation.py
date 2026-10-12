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
