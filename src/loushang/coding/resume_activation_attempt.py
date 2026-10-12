"""Coding-owned, inert activation attempt fact for a resumed user input.

An attempt records the activation selected by its owner. It is neither
current authority nor evidence that an effect or user input completed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from loushang.foundation.json import JSONValue, dump_json_value, require_json_mapping
from loushang.harness.transcript.kinds import EXTENSION_DATA_KIND
from loushang.harness.transcript.types import AgentTranscriptRecord, ExtensionData
from loushang.harness.transcript.writer import AgentTranscriptRecordFactory

CODING_ACTIVATION_ATTEMPT_EXTENSION_TYPE = "coding.activation-attempt/v1"
CODING_ACTIVATION_ATTEMPT_MAX_BYTES = 4096

_IDENTIFIER = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_EFFECT_CODE = re.compile(r"[a-z][a-z0-9._-]{0,63}\Z")
_FIELDS = frozenset({
    "version", "attemptId", "requestId", "sessionId", "originalLeafId",
    "ancestryDigest", "planFingerprint", "epochFingerprint", "subjectDigest",
    "effectClasses",
})


@dataclass(frozen=True, slots=True)
class CodingActivationAttemptV1:
    """Bounded historical intent, without approval or effect-settlement meaning."""

    attempt_id: str
    request_id: str
    session_id: str
    original_leaf_id: str | None
    ancestry_digest: str
    plan_fingerprint: str
    epoch_fingerprint: str
    subject_digest: str
    effect_classes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("attempt_id", "request_id", "session_id"):
            value = getattr(self, name)
            if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
                raise ValueError(f"activation attempt {name} is invalid")
        if self.original_leaf_id is not None and (
            type(self.original_leaf_id) is not str
            or _IDENTIFIER.fullmatch(self.original_leaf_id) is None
        ):
            raise ValueError("activation attempt original leaf is invalid")
        for name in (
            "ancestry_digest", "plan_fingerprint", "epoch_fingerprint",
            "subject_digest",
        ):
            value = getattr(self, name)
            if type(value) is not str or _DIGEST.fullmatch(value) is None:
                raise ValueError(f"activation attempt {name} is invalid")
        codes = self.effect_classes
        if (
            type(codes) is not tuple or len(codes) > 16
            or any(type(code) is not str or _EFFECT_CODE.fullmatch(code) is None
                   for code in codes)
            or codes != tuple(sorted(set(codes)))
        ):
            raise ValueError("activation attempt effect classes are invalid")
        if len(_encoded(self.to_data())) > CODING_ACTIVATION_ATTEMPT_MAX_BYTES:
            raise ValueError("activation attempt exceeds its byte budget")

    def to_data(self) -> dict[str, JSONValue]:
        return {
            "version": 1,
            "attemptId": self.attempt_id,
            "requestId": self.request_id,
            "sessionId": self.session_id,
            "originalLeafId": self.original_leaf_id,
            "ancestryDigest": self.ancestry_digest,
            "planFingerprint": self.plan_fingerprint,
            "epochFingerprint": self.epoch_fingerprint,
            "subjectDigest": self.subject_digest,
            "effectClasses": list(self.effect_classes),
        }


def prepare_coding_activation_attempt_record(
    attempt: CodingActivationAttemptV1, *, created_at: datetime,
) -> AgentTranscriptRecord:
    """Build a fixed-ID intent after admission; committing belongs to Transcript."""

    if not isinstance(attempt, CodingActivationAttemptV1):
        raise TypeError("activation attempt record requires a Coding attempt")
    record = AgentTranscriptRecordFactory(
        clock=lambda: created_at,
        id_factory=lambda: attempt.attempt_id,
    ).create(
        EXTENSION_DATA_KIND,
        ExtensionData(CODING_ACTIVATION_ATTEMPT_EXTENSION_TYPE, attempt.to_data()),
        parent_id=attempt.original_leaf_id,
    )
    validate_coding_activation_attempt_record(record)
    return record


def validate_coding_activation_attempt_record(
    record: AgentTranscriptRecord,
) -> CodingActivationAttemptV1:
    """Decode an exact v1 selected-path fact; reject unknown or malformed intent."""

    if record.kind != EXTENSION_DATA_KIND or not isinstance(record.payload, ExtensionData):
        raise ValueError("activation attempt requires an extension data record")
    payload = record.payload
    if payload.extension_type != CODING_ACTIVATION_ATTEMPT_EXTENSION_TYPE:
        raise ValueError("activation attempt extension type is invalid")
    raw = payload.data
    if not isinstance(raw, dict) or set(raw) != _FIELDS:
        raise ValueError("activation attempt fields are invalid")
    data = require_json_mapping(raw, name="activation attempt")
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("activation attempt version is invalid")
    effects = data["effectClasses"]
    if not isinstance(effects, list):
        raise ValueError("activation attempt effect classes are invalid")
    attempt = CodingActivationAttemptV1(
        attempt_id=cast(str, data["attemptId"]),
        request_id=cast(str, data["requestId"]),
        session_id=cast(str, data["sessionId"]),
        original_leaf_id=cast(str | None, data["originalLeafId"]),
        ancestry_digest=cast(str, data["ancestryDigest"]),
        plan_fingerprint=cast(str, data["planFingerprint"]),
        epoch_fingerprint=cast(str, data["epochFingerprint"]),
        subject_digest=cast(str, data["subjectDigest"]),
        effect_classes=cast(tuple[str, ...], tuple(effects)),
    )
    if record.record_id != attempt.attempt_id or record.parent_id != attempt.original_leaf_id:
        raise ValueError("activation attempt record identity or parent differs")
    return attempt


def _encoded(value: object) -> bytes:
    return dump_json_value(
        value, name="activation attempt", ensure_ascii=True, sort_keys=True,
    ).encode("utf-8")


__all__ = [
    "CODING_ACTIVATION_ATTEMPT_EXTENSION_TYPE",
    "CODING_ACTIVATION_ATTEMPT_MAX_BYTES",
    "CodingActivationAttemptV1",
    "prepare_coding_activation_attempt_record",
    "validate_coding_activation_attempt_record",
]
