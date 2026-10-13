"""Bind Coding Resume intent context to the original Worker C5 owner."""

from __future__ import annotations

from collections.abc import Mapping

from loushang.harness.resume_effects import ResumeEffectParentContextV1
from loushang.harness.worker.product_activation import (
    ProductWorkerActivationCoordinator,
    ProductWorkerActivationReceiptV1,
    _ActivationRejected,
)


class CodingWorkerResumeParentError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _snapshot(
    coordinator: ProductWorkerActivationCoordinator,
    context: ResumeEffectParentContextV1,
) -> Mapping[str, object] | None:
    try:
        return coordinator.resume_parent_snapshot(context)
    except _ActivationRejected as error:
        if error.reason.value == "resume_parent_unknown":
            return None
        raise


def enroll_coding_worker_resume_parent(
    *,
    coordinator: ProductWorkerActivationCoordinator,
    receipt: ProductWorkerActivationReceiptV1,
    context: ResumeEffectParentContextV1 | None,
) -> Mapping[str, object] | None:
    """Enroll or recover the exact durable parent before payload preparation."""

    if context is None:
        return None
    if (
        type(context) is not ResumeEffectParentContextV1
        or context.product_id != receipt.policy.product_id
        or context.owner_id != "harness.worker-activation"
        or context.scope_digest
        != coordinator.resume_parent_scope_digest(
            product_id=receipt.policy.product_id,
            product_scope_id=receipt.policy.product_scope_id,
        )
        or context.contract_digest != coordinator.resume_parent_contract_digest
    ):
        raise CodingWorkerResumeParentError(
            "coding_worker_resume_parent_context_mismatch"
        )
    existing = _snapshot(coordinator, context)
    if existing is not None:
        if existing["sealed"] is True:
            raise CodingWorkerResumeParentError(
                "coding_worker_resume_parent_already_sealed"
            )
        return existing
    state = coordinator.snapshot()
    revision = state.get("stateRevision")
    if type(revision) is not int or revision < 1:
        raise CodingWorkerResumeParentError("coding_worker_resume_parent_state_invalid")
    try:
        coordinator.enroll_resume_parent(
            context,
            policy=receipt.policy,
            expected_state_revision=revision,
        )
    except Exception:
        # A failed durable acknowledgement may still have committed the exact
        # parent. Re-read the original owner before deciding that it is unknown.
        recovered = _snapshot(coordinator, context)
        if recovered is None:
            raise
        if recovered["sealed"] is True:
            raise CodingWorkerResumeParentError(
                "coding_worker_resume_parent_already_sealed"
            )
        return recovered
    enrolled = _snapshot(coordinator, context)
    if enrolled is None:
        raise CodingWorkerResumeParentError(
            "coding_worker_resume_parent_enrollment_unknown"
        )
    return enrolled


def seal_coding_worker_resume_parent(
    *,
    coordinator: ProductWorkerActivationCoordinator,
    context: ResumeEffectParentContextV1 | None,
) -> Mapping[str, object] | None:
    """Seal the exact native membership after Worker C5 publication."""

    if context is None:
        return None
    snapshot = _snapshot(coordinator, context)
    if snapshot is None:
        raise CodingWorkerResumeParentError("coding_worker_resume_parent_missing")
    if snapshot["sealed"] is True:
        return snapshot
    native_attempts = snapshot["nativeAttempts"]
    if not isinstance(native_attempts, Mapping) or not native_attempts:
        raise CodingWorkerResumeParentError(
            "coding_worker_resume_parent_membership_empty"
        )
    revision = snapshot["stateRevision"]
    if type(revision) is not int or revision < 1:
        raise CodingWorkerResumeParentError("coding_worker_resume_parent_state_invalid")
    return coordinator.seal_resume_parent(
        context,
        expected_state_revision=revision,
    )


__all__ = [
    "CodingWorkerResumeParentError",
    "enroll_coding_worker_resume_parent",
    "seal_coding_worker_resume_parent",
]
