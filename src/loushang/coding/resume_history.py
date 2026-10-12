"""Read-only Coding Resume Header projection, without execution admission."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from loushang.harness.conversation import ConversationHeader, ConversationRepository
from loushang.harness.runtime import RuntimeProfileSnapshot
from loushang.harness.transcript.jsonl_file import (
    load_agent_transcript_file,
    load_agent_transcript_header,
)
from loushang.harness.transcript.session_catalog import (
    session_file_authority_fingerprint,
)
from loushang.harness.transcript.types import AgentTranscriptRecord

from .composition_provenance import (
    CodingCompositionProvenanceV1,
    historical_composition_provenance,
    historical_startup_composition_record,
)
from .product_plan import (
    CODING_CAPABILITY_PROFILE_METADATA_KEY,
    CODING_PRODUCT_ID,
    CODING_TRANSCRIPT_RUNTIME,
)
from .resume_binding import (
    CodingRuntimeBindingV1,
    project_coding_runtime_binding_path,
)


@dataclass(frozen=True, slots=True)
class CodingResumeHeaderPreview:
    """A bounded Header observation, never proof of a writable Session."""

    header: ConversationHeader
    product_identity: Literal["coding", "unknown"]
    composition: CodingCompositionProvenanceV1 | None


@dataclass(frozen=True, slots=True)
class CodingResumeHistoryPreview:
    """A bounded read-only transcript snapshot, never an execution snapshot."""

    header_preview: CodingResumeHeaderPreview
    records: tuple[AgentTranscriptRecord, ...]
    selected_records: tuple[AgentTranscriptRecord, ...]
    selected_leaf_id: str | None
    startup: dict[str, object] | None
    provenance_conflict: bool
    binding_status: Literal["none", "bound", "unknown_version", "invalid"]
    binding: CodingRuntimeBindingV1 | None
    selected_ancestry_digest: str | None
    source_fingerprint: str
    status: Literal["preview"] = "preview"


def inspect_coding_resume_header(
    header: ConversationHeader,
) -> CodingResumeHeaderPreview:
    """Classify historical evidence without resolving the installed composition."""

    runtime = CODING_TRANSCRIPT_RUNTIME.read_snapshot(header.metadata)
    raw_capability = header.metadata.get(CODING_CAPABILITY_PROFILE_METADATA_KEY)
    capability = (
        None
        if raw_capability is None
        else RuntimeProfileSnapshot.from_json(raw_capability)
    )
    if capability is not None and capability.product_id != CODING_PRODUCT_ID:
        raise ValueError(
            "Coding cannot view a session with a capability profile for Product "
            f"{capability.product_id!r}"
        )
    return CodingResumeHeaderPreview(
        header=header,
        product_identity=(
            "coding" if runtime is not None or capability is not None else "unknown"
        ),
        composition=historical_composition_provenance(header.metadata),
    )


def read_coding_resume_header(path: str | Path) -> CodingResumeHeaderPreview:
    """Read an admitted Session path without a Writer, repair, or lock file."""

    return inspect_coding_resume_header(
        load_agent_transcript_header(Path(path), read_only=True)
    )


def read_coding_resume_snapshot(
    path: str | Path, *, max_bytes: int, selected_leaf_id: str | None = None,
    expected_source_fingerprint: str | None = None,
) -> CodingResumeHistoryPreview:
    """Read a bounded historical snapshot without acquiring transcript authority."""

    if type(max_bytes) is not int or not 1 <= max_bytes <= 8 * 1024 * 1024:
        raise ValueError("Coding Resume snapshot budget must be within 1 to 8 MiB")
    source_path = Path(path)
    source_fingerprint = session_file_authority_fingerprint(source_path)
    if (
        expected_source_fingerprint is not None
        and source_fingerprint != expected_source_fingerprint
    ):
        raise ValueError("Coding Resume source changed before snapshot")
    header, records = load_agent_transcript_file(
        source_path, max_bytes=max_bytes, read_only=True,
    )
    if session_file_authority_fingerprint(source_path) != source_fingerprint:
        raise ValueError("Coding Resume source changed during snapshot")
    header_preview = inspect_coding_resume_header(header)
    repository = ConversationRepository.create(
        header=header,
        records=records,
        record_id=lambda record: record.record_id,
        parent_id=lambda record: record.parent_id,
        leaf_id=selected_leaf_id,
    )
    startup = historical_startup_composition_record(records)
    composition = header_preview.composition
    selected_records = repository.active_records()
    try:
        binding_projection = project_coding_runtime_binding_path(
            selected_records, current_session_id=header.conversation_id,
        )
        binding_status: Literal["none", "bound", "unknown_version", "invalid"] = (
            binding_projection.status
        )
        binding = binding_projection.binding
        ancestry_digest = binding_projection.ancestry_digest
    except ValueError:
        # Historical viewing remains possible when binding evidence is unusable.
        binding_status = "invalid"
        binding = None
        ancestry_digest = None
    return CodingResumeHistoryPreview(
        header_preview=header_preview,
        records=tuple(records),
        selected_records=selected_records,
        selected_leaf_id=repository.leaf_id,
        startup=startup,
        provenance_conflict=(
            startup is not None
            and composition is not None
            and (
                startup["setId"] != composition.set_id
                or startup["planFingerprint"] != composition.plan_fingerprint
            )
        ),
        binding_status=binding_status,
        binding=binding,
        selected_ancestry_digest=ancestry_digest,
        source_fingerprint=source_fingerprint,
    )


__all__ = [
    "CodingResumeHeaderPreview",
    "CodingResumeHistoryPreview",
    "inspect_coding_resume_header",
    "read_coding_resume_header",
    "read_coding_resume_snapshot",
]
