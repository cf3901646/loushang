"""Read-only Coding Resume Header projection, without execution admission."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from loushang.harness.conversation import ConversationHeader
from loushang.harness.runtime import RuntimeProfileSnapshot
from loushang.harness.transcript.jsonl_file import (
    load_agent_transcript_file,
    load_agent_transcript_header,
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
    startup: dict[str, object] | None
    provenance_conflict: bool
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
    path: str | Path, *, max_bytes: int,
) -> CodingResumeHistoryPreview:
    """Read a bounded historical snapshot without acquiring transcript authority."""

    if type(max_bytes) is not int or not 1 <= max_bytes <= 8 * 1024 * 1024:
        raise ValueError("Coding Resume snapshot budget must be within 1 to 8 MiB")
    header, records = load_agent_transcript_file(
        Path(path), max_bytes=max_bytes, read_only=True,
    )
    header_preview = inspect_coding_resume_header(header)
    startup = historical_startup_composition_record(records)
    composition = header_preview.composition
    return CodingResumeHistoryPreview(
        header_preview=header_preview,
        records=tuple(records),
        startup=startup,
        provenance_conflict=(
            startup is not None
            and composition is not None
            and (
                startup["setId"] != composition.set_id
                or startup["planFingerprint"] != composition.plan_fingerprint
            )
        ),
    )


__all__ = [
    "CodingResumeHeaderPreview",
    "CodingResumeHistoryPreview",
    "inspect_coding_resume_header",
    "read_coding_resume_header",
    "read_coding_resume_snapshot",
]
