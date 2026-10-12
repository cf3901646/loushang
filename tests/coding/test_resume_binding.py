from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from loushang.ai.types import UserMessage
from loushang.coding.composition_provenance import CodingCompositionProvenanceV1
from loushang.coding.resume_binding import (
    CODING_RUNTIME_BINDING_METADATA_KEY,
    CodingRuntimeBindingV1,
    coding_user_payload_digest,
    inspect_coding_runtime_binding,
    prepare_coding_resume_user_record,
    validate_coding_runtime_binding_record,
)
from loushang.coding.session_manager import SessionManager
from loushang.harness.transcript.jsonl_file import load_agent_transcript_file


def _binding() -> CodingRuntimeBindingV1:
    return CodingRuntimeBindingV1(
        attempt_id="attempt-1",
        input_id="input-1",
        record_id="record-1",
        session_id="session-1",
        original_leaf_id="leaf-1",
        ancestry_digest="a" * 64,
        subject_digest="b" * 64,
        origin_composition=CodingCompositionProvenanceV1("retired-set", "c" * 64),
        planned_fingerprint="d" * 64,
        actual_fingerprint="e" * 64,
        payload_digest="f" * 64,
        difference_codes=("plugin.changed", "policy.tightened"),
    )


def test_runtime_binding_round_trip_keeps_historical_origin_and_bounded_metadata() -> None:
    binding = _binding()
    metadata = binding.to_message_metadata()

    observation = inspect_coding_runtime_binding(metadata)

    assert observation.status == "known"
    assert observation.binding == binding
    assert tuple(metadata) == (CODING_RUNTIME_BINDING_METADATA_KEY,)
    assert len(str(metadata).encode()) < 4096
    assert "retired-set" in str(metadata)
    assert "Credential" not in str(metadata)


def test_runtime_binding_preserves_legacy_unknown_and_unknown_schema_is_inert() -> None:
    binding = replace(_binding(), origin_composition=None, difference_codes=())
    metadata = binding.to_message_metadata()
    assert metadata[CODING_RUNTIME_BINDING_METADATA_KEY]["originEvidence"] == {
        "kind": "legacy_unknown"
    }
    assert inspect_coding_runtime_binding(metadata).binding == binding
    assert inspect_coding_runtime_binding({}).status == "absent"

    unknown = {CODING_RUNTIME_BINDING_METADATA_KEY: {"version": 2, "future": "value"}}
    result = inspect_coding_runtime_binding(unknown)
    assert result.status == "unknown_version"
    assert result.binding is None
    assert unknown[CODING_RUNTIME_BINDING_METADATA_KEY] == {
        "version": 2,
        "future": "value",
    }


@pytest.mark.parametrize(
    "change",
    [
        {"attempt_id": "contains spaces"},
        {"ancestry_digest": "A" * 64},
        {"difference_codes": ("permission=full_access",)},
        {"difference_codes": tuple(f"change.{index}" for index in range(17))},
        {"origin_composition": CodingCompositionProvenanceV1("x" * 4096, "c" * 64)},
    ],
)
def test_runtime_binding_rejects_unbounded_or_non_redacted_fields(change) -> None:
    with pytest.raises((TypeError, ValueError)):
        replace(_binding(), **change)


def test_runtime_binding_rejects_malformed_known_schema_without_authorizing_it() -> None:
    metadata = _binding().to_message_metadata()
    raw = dict(metadata[CODING_RUNTIME_BINDING_METADATA_KEY])
    raw["extraGrant"] = "full_access"
    with pytest.raises(ValueError):
        inspect_coding_runtime_binding({CODING_RUNTIME_BINDING_METADATA_KEY: raw})


def test_binding_and_resource_evidence_share_one_validated_user_record() -> None:
    message = UserMessage(role="user", content="continue", timestamp=1.0)
    binding = replace(_binding(), payload_digest=coding_user_payload_digest(message))
    record = prepare_coding_resume_user_record(
        binding,
        message,
        commit_parent_id="activation-intent-1",
        created_at=datetime(2026, 10, 12, tzinfo=UTC),
        resource_metadata={"loushang.request.resource_evidence": {"schemaVersion": 1}},
    )

    assert record.record_id == binding.record_id
    assert record.parent_id == "activation-intent-1"
    assert set(record.metadata) == {
        CODING_RUNTIME_BINDING_METADATA_KEY,
        "loushang.request.resource_evidence",
    }
    assert validate_coding_runtime_binding_record(
        record, expected_session_id=binding.session_id,
    ) == binding
    with pytest.raises(ValueError, match="payload digest"):
        validate_coding_runtime_binding_record(
            replace(record, payload=replace(message, content="changed")),
            expected_session_id=binding.session_id,
        )
    with pytest.raises(ValueError, match="metadata key conflict"):
        prepare_coding_resume_user_record(
            binding,
            message,
            commit_parent_id=None,
            created_at=datetime(2026, 10, 12, tzinfo=UTC),
            resource_metadata={CODING_RUNTIME_BINDING_METADATA_KEY: {}},
        )


def test_runtime_binding_and_resource_evidence_survive_one_jsonl_commit(tmp_path) -> None:
    async def scenario() -> None:
        manager = await SessionManager.new(
            session_dir=tmp_path,
            cwd=str(tmp_path),
            defer_materialization=False,
        )
        try:
            message = UserMessage(role="user", content="continue", timestamp=1.0)
            binding = replace(
                _binding(),
                session_id=manager.header.conversation_id,
                original_leaf_id=manager.leaf_id,
                payload_digest=coding_user_payload_digest(message),
            )
            record = prepare_coding_resume_user_record(
                binding,
                message,
                commit_parent_id=manager.leaf_id,
                created_at=datetime(2026, 10, 12, tzinfo=UTC),
                resource_metadata={
                    "loushang.request.resource_evidence": {"schemaVersion": 1}
                },
            )
            first = await manager.commit_prebuilt_user_message(record)
            duplicate = await manager.commit_prebuilt_user_message(record)
            assert first.disposition == "committed"
            assert duplicate.disposition == "already_committed"
            path = manager.session_file
            assert path is not None
        finally:
            await manager.dispose_runtime_profile()

        _, records = load_agent_transcript_file(path, read_only=True)
        assert len(records) == 1
        assert records[0].metadata["loushang.request.resource_evidence"] == {
            "schemaVersion": 1
        }
        assert validate_coding_runtime_binding_record(
            records[0], expected_session_id=binding.session_id,
        ) == binding

    asyncio.run(scenario())
