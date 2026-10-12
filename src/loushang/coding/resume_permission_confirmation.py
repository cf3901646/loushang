"""Coding permission-expansion confirmation through the native Approval owner.

This is one prerequisite of current Resume admission. It does not compute the
actor's current policy or settle activation effects, and grants no Tool scope.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from loushang.foundation.json import dump_json_value
from loushang.harness.approval import (
    ApprovalConfirmation,
    ApprovalGrantProposal,
    ApprovalRequest,
    InteractiveApprovalResolver,
    ensure_approval_action_id,
)

from .resume_activation_attempt import CodingActivationAttemptV1

_EXPANSION = re.compile(r"[a-z][a-z0-9._-]{0,63}\Z")


def coding_resume_permission_request(
    attempt: CodingActivationAttemptV1, *, actor_id: str,
    expansion_codes: tuple[str, ...], action_id: str | None = None,
) -> ApprovalRequest:
    """Bind owner-observed expansion to this exact subject, target and candidate.

    Expansion classification and current subject/policy verification belong to
    their original owners. Unknown authority must be represented explicitly,
    rather than treating configuration or historical receipts as confirmation.
    """

    if not isinstance(attempt, CodingActivationAttemptV1):
        raise TypeError("Coding Resume confirmation requires an activation attempt")
    if (
        type(expansion_codes) is not tuple or not 1 <= len(expansion_codes) <= 16
        or any(type(code) is not str or _EXPANSION.fullmatch(code) is None for code in expansion_codes)
        or expansion_codes != tuple(sorted(set(expansion_codes)))
    ):
        raise ValueError("Coding Resume permission expansion codes are invalid")
    arguments = {**attempt.to_data(), "permissionExpansion": list(expansion_codes)}
    encoded = dump_json_value(
        arguments, name="Coding Resume permission confirmation",
        ensure_ascii=True, sort_keys=True,
    ).encode("utf-8")
    fingerprint = hashlib.sha256(
        b"loushang.coding.resume-permission-confirmation/v1\0" + encoded,
    ).hexdigest()
    return ensure_approval_action_id(ApprovalRequest(
        tool_name="resume", actor_id=actor_id, action_id=action_id,
        action_fingerprint=fingerprint, arguments=arguments,
        policy_code="resume_permission_expansion",
        reason="Confirm the current permissions for this resumed session: " + ", ".join(expansion_codes),
        session_grant=ApprovalGrantProposal(
            capability="coding.resume.permission-expansion",
            constraints=(("confirmationFingerprint", fingerprint),),
            summary="Use these permissions for this exact Resume candidate",
        ),
    ))


@dataclass(frozen=True, slots=True)
class CodingResumePermissionConfirmation:
    """Borrow an exact native confirmation; never persist it as authority."""

    attempt: CodingActivationAttemptV1
    actor_id: str
    expansion_codes: tuple[str, ...]
    owner: InteractiveApprovalResolver
    confirmation: ApprovalConfirmation

    def require_current(self, attempt: CodingActivationAttemptV1) -> None:
        if attempt != self.attempt:
            raise PermissionError("Coding Resume permission confirmation target changed")
        expected = coding_resume_permission_request(
            attempt, actor_id=self.actor_id, expansion_codes=self.expansion_codes,
            action_id=self.confirmation.request.action_id,
        )
        self.owner.require_current_confirmation(self.confirmation, request=expected)
