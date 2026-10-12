from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import replace

import pytest

from loushang.coding.composition_provenance import CODING_COMPOSITION_HEADER_KEY
from loushang.coding.product_plan import (
    CODING_CAPABILITY_PROFILE_METADATA_KEY,
    CODING_RUNTIME_PROFILE_METADATA_KEY,
)
from loushang.coding.resume_history import (
    inspect_coding_resume_header,
    read_coding_resume_header,
    read_coding_resume_snapshot,
)
from loushang.coding.session_manager import SessionManager
from loushang.harness.transcript.jsonl_file import (
    AgentTranscriptFileError,
    load_agent_transcript_file,
    write_agent_transcript_export,
)


def test_readonly_resume_header_survives_retired_composition_and_profile_change(
    tmp_path,
) -> None:
    async def create() -> object:
        manager = await SessionManager.new_with_composition(
            session_dir=tmp_path,
            cwd=str(tmp_path),
            composition_set="coding-minimal",
            defer_materialization=False,
        )
        try:
            return manager.session_file
        finally:
            await manager.dispose_runtime_profile()

    path = asyncio.run(create())
    assert path is not None
    header, records = load_agent_transcript_file(path, read_only=True)
    metadata = deepcopy(dict(header.metadata))
    metadata[CODING_COMPOSITION_HEADER_KEY] = {
        "version": 1,
        "setId": "retired-coding-set",
        "planFingerprint": "a" * 64,
    }
    capability = metadata[CODING_CAPABILITY_PROFILE_METADATA_KEY]
    assert isinstance(capability, dict)
    capability["capabilities"] = []
    write_agent_transcript_export(path, replace(header, metadata=metadata), records)
    before = {item.name: item.read_bytes() for item in tmp_path.iterdir() if item.is_file()}

    preview = read_coding_resume_header(path)

    assert preview.header.conversation_id == header.conversation_id
    assert preview.product_identity == "coding"
    assert preview.composition is not None
    assert preview.composition.set_id == "retired-coding-set"
    assert preview.composition.plan_fingerprint == "a" * 64
    assert {item.name: item.read_bytes() for item in tmp_path.iterdir() if item.is_file()} == before


def test_readonly_resume_header_marks_missing_composition_as_legacy_unknown(
    tmp_path,
) -> None:
    async def create() -> object:
        manager = await SessionManager.new(
            session_dir=tmp_path,
            cwd=str(tmp_path),
            defer_materialization=False,
        )
        try:
            return manager.session_file
        finally:
            await manager.dispose_runtime_profile()

    path = asyncio.run(create())
    assert path is not None

    preview = read_coding_resume_header(path)

    assert preview.product_identity == "coding"
    assert preview.composition is None

    metadata = dict(preview.header.metadata)
    metadata.pop(CODING_RUNTIME_PROFILE_METADATA_KEY)
    metadata.pop(CODING_CAPABILITY_PROFILE_METADATA_KEY)
    unknown = inspect_coding_resume_header(
        replace(preview.header, metadata=metadata)
    )
    assert unknown.product_identity == "unknown"

    foreign = deepcopy(dict(preview.header.metadata))
    capability = foreign[CODING_CAPABILITY_PROFILE_METADATA_KEY]
    assert isinstance(capability, dict)
    capability["productId"] = "another-product"
    with pytest.raises(ValueError, match="another-product"):
        inspect_coding_resume_header(replace(preview.header, metadata=foreign))

    with path.open("ab") as stream:
        stream.write(b'{"type":')
    before = path.read_bytes()
    history = read_coding_resume_snapshot(path, max_bytes=1024 * 1024)
    assert history.status == "preview"
    assert history.records == ()
    assert path.read_bytes() == before
    with pytest.raises(AgentTranscriptFileError, match="read budget"):
        read_coding_resume_snapshot(path, max_bytes=1)
    assert path.read_bytes() == before
