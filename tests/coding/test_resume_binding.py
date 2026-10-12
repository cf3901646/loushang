from __future__ import annotations

import asyncio
import base64
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from loushang.ai.types import ImagePart, UserMessage
from loushang.coding.composition_provenance import CodingCompositionProvenanceV1
from loushang.coding.resume_binding import (
    CODING_RUNTIME_BINDING_METADATA_KEY,
    CodingRuntimeBindingV1,
    coding_user_payload_digest,
    inspect_coding_runtime_binding,
    prepare_coding_resume_user_record,
    project_coding_runtime_binding_path,
    validate_coding_runtime_binding_record,
)
from loushang.coding.session_manager import SessionManager
from loushang.harness.conversation.repository import ConversationRepository
from loushang.harness.transcript.jsonl_file import load_agent_transcript_file
from loushang.harness.transcript.kinds import CONTEXT_COMPACTION_CHECKPOINT_KIND
from loushang.harness.transcript.types import (
    ContextCompactionCheckpoint,
    SessionImagePart,
)
from loushang.harness.transcript.writer import AgentTranscriptRecordFactory


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


def test_resume_user_commit_externalizes_image_before_binding_payload_digest(
    tmp_path,
) -> None:
    async def scenario() -> None:
        manager = await SessionManager.new(
            session_dir=tmp_path,
            cwd=str(tmp_path),
            defer_materialization=False,
        )
        message = UserMessage(
            role="user",
            content=[ImagePart(
                type="image", mime_type="image/png",
                data=base64.b64encode(b"resume-image").decode("ascii"),
            )],
            timestamp=1.0,
        )
        try:
            def prepare(persisted: UserMessage):
                assert isinstance(persisted.content, list)
                assert isinstance(persisted.content[0], SessionImagePart)
                binding = replace(
                    _binding(),
                    session_id=manager.header.conversation_id,
                    original_leaf_id=manager.leaf_id,
                    payload_digest=coding_user_payload_digest(persisted),
                )
                return prepare_coding_resume_user_record(
                    binding, persisted,
                    commit_parent_id=manager.leaf_id,
                    created_at=datetime(2026, 10, 12, tzinfo=UTC),
                    resource_metadata={"loushang.request.resource_evidence": {
                        "schemaVersion": 1,
                    }},
                )

            result = await manager.commit_prebuilt_user_message_from_message(
                message, prepare_record=prepare,
            )
            assert result.disposition == "committed"
            path = manager.session_file
            assert path is not None
        finally:
            await manager.dispose_runtime_profile()

        _, records = load_agent_transcript_file(path, read_only=True)
        assert len(records) == 1
        assert isinstance(records[0].payload.content, list)
        assert isinstance(records[0].payload.content[0], SessionImagePart)
        assert validate_coding_runtime_binding_record(
            records[0], expected_session_id=manager.header.conversation_id,
        ).payload_digest == coding_user_payload_digest(records[0].payload)
        assert records[0].metadata["loushang.request.resource_evidence"] == {
            "schemaVersion": 1,
        }

    asyncio.run(scenario())


def test_runtime_binding_projection_tracks_selected_branch_across_compaction() -> None:
    message = UserMessage(role="user", content="continue", timestamp=1.0)
    first = AgentTranscriptRecordFactory(
        clock=lambda: datetime(2026, 10, 12, tzinfo=UTC),
        id_factory=lambda: "initial",
    ).create("agent.message", message, parent_id=None)
    binding = replace(
        _binding(), original_leaf_id=first.record_id,
        payload_digest=coding_user_payload_digest(message),
    )
    bound = prepare_coding_resume_user_record(
        binding, message, commit_parent_id=first.record_id,
        created_at=datetime(2026, 10, 12, tzinfo=UTC),
    )
    checkpoint = AgentTranscriptRecordFactory(
        clock=lambda: datetime(2026, 10, 12, tzinfo=UTC),
        id_factory=lambda: "checkpoint",
    ).create(
        CONTEXT_COMPACTION_CHECKPOINT_KIND,
        ContextCompactionCheckpoint(
            summary="earlier context", first_kept_record_id=bound.record_id,
            tokens_before=100,
        ),
        parent_id=bound.record_id,
    )
    alternate = replace(checkpoint, record_id="alternate", parent_id=first.record_id)
    repository = ConversationRepository.create(
        header=None, records=(first, bound, checkpoint, alternate),
        record_id=lambda record: record.record_id,
        parent_id=lambda record: record.parent_id,
        leaf_id=checkpoint.record_id,
    )

    projected = project_coding_runtime_binding_path(
        repository.active_records(), current_session_id=binding.session_id,
    )
    assert projected.status == "bound"
    assert projected.binding == binding
    assert projected.record_id == bound.record_id
    assert len(projected.ancestry_digest) == 64

    repository.branch(alternate.record_id)
    alternate_projection = project_coding_runtime_binding_path(
        repository.active_records(), current_session_id=binding.session_id,
    )
    assert alternate_projection.status == "none"
    assert alternate_projection.ancestry_digest != projected.ancestry_digest


def test_runtime_binding_projection_does_not_inherit_fork_origin() -> None:
    message = UserMessage(role="user", content="continue", timestamp=1.0)
    binding = replace(
        _binding(), original_leaf_id=None,
        payload_digest=coding_user_payload_digest(message),
    )
    source_record = prepare_coding_resume_user_record(
        binding, message, commit_parent_id=None,
        created_at=datetime(2026, 10, 12, tzinfo=UTC),
    )
    assert project_coding_runtime_binding_path(
        (source_record,), current_session_id="fork-session",
    ).status == "none"
    target_binding = replace(
        binding, record_id="target-record", session_id="fork-session",
        original_leaf_id=source_record.record_id,
    )
    target_record = prepare_coding_resume_user_record(
        target_binding, message, commit_parent_id=source_record.record_id,
        created_at=datetime(2026, 10, 12, tzinfo=UTC),
    )
    assert project_coding_runtime_binding_path(
        (source_record, target_record), current_session_id="fork-session",
    ).binding == target_binding


def test_runtime_binding_projection_fails_closed_on_unknown_or_corrupt_path() -> None:
    message = UserMessage(role="user", content="continue", timestamp=1.0)
    binding = replace(
        _binding(), original_leaf_id=None,
        payload_digest=coding_user_payload_digest(message),
    )
    bound = prepare_coding_resume_user_record(
        binding, message, commit_parent_id=None,
        created_at=datetime(2026, 10, 12, tzinfo=UTC),
    )
    unknown = replace(
        bound, record_id="future", parent_id=bound.record_id,
        metadata={CODING_RUNTIME_BINDING_METADATA_KEY: {"version": 2}},
    )
    projected = project_coding_runtime_binding_path(
        (bound, unknown), current_session_id=binding.session_id,
    )
    assert projected.status == "unknown_version"
    assert projected.binding is None
    assert projected.record_id == unknown.record_id
    assert len(projected.ancestry_digest) == 64

    later_binding = replace(
        binding, record_id="later", original_leaf_id=unknown.record_id,
    )
    later = prepare_coding_resume_user_record(
        later_binding, message, commit_parent_id=unknown.record_id,
        created_at=datetime(2026, 10, 12, tzinfo=UTC),
    )
    assert project_coding_runtime_binding_path(
        (bound, unknown, later), current_session_id=binding.session_id,
    ).binding == later_binding

    with pytest.raises(ValueError, match="payload digest"):
        project_coding_runtime_binding_path(
            (replace(bound, payload=replace(message, content="tampered")),),
            current_session_id=binding.session_id,
        )
    with pytest.raises(ValueError, match="complete parent-linked"):
        project_coding_runtime_binding_path(
            (unknown,), current_session_id=binding.session_id,
        )
    with pytest.raises(ValueError, match="agent UserMessage"):
        project_coding_runtime_binding_path(
            (replace(bound, kind=CONTEXT_COMPACTION_CHECKPOINT_KIND),),
            current_session_id=binding.session_id,
        )
