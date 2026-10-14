from __future__ import annotations

import asyncio
import sys

import pytest

from loushang.ai.types import UserMessage
from loushang.coding.bootstrap import (
    create_agent_session_runtime,
    create_services,
)
from loushang.coding.composition_provenance import startup_composition_record
from loushang.harness.config.agent import ControlConfig, SettingsManager
from loushang.harness.transcript import load_agent_transcript_file


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="native macOS legacy same-ID Resume evidence",
)
def test_darwin_legacy_resume_uses_current_resources_without_rewriting_history(
    tmp_path,
    monkeypatch,
    record_testsuite_property,
):
    monkeypatch.setenv("LOUSHANG_HOME", str(tmp_path / "home"))
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    agents = workspace / "AGENTS.md"
    agents.write_text("Initial workspace instructions.\n", encoding="utf-8")
    skill = workspace / "skills" / "review" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: review\ndescription: Review code\n---\nReview carefully.\n",
        encoding="utf-8",
    )
    session_dir = tmp_path / "home/data/sessions"
    record_testsuite_property("native_platform", sys.platform)
    record_testsuite_property("resume_route", "legacy-same-id")

    async def scenario():
        original_runtime = create_agent_session_runtime(
            session_dir=session_dir,
            composition_set="coding-standard",
        )
        assert original_runtime._owned_transcript_factory is None
        try:
            original = await original_runtime.create_session(cwd=str(workspace))
            await original.session_manager.append_message(
                UserMessage(role="user", content="before resource change", timestamp=1.0)
            )
            session_file = original.session_manager.session_file
            assert session_file is not None
            session_id = original.session_id
            header = original.session_manager.header
            historical_receipt = startup_composition_record(
                original.session_manager.get_entries()
            )
            assert historical_receipt is not None
        finally:
            await original_runtime.dispose_session_runtime()

        agents.write_text("Updated workspace instructions.\n", encoding="utf-8")
        changed_services = create_services(
            settings_manager=SettingsManager(
                ControlConfig(disabled_skills=("review",))
            )
        )
        resumed_runtime = create_agent_session_runtime(
            session_dir=session_dir,
            composition_set="coding-standard",
            services=changed_services,
        )
        assert resumed_runtime._owned_transcript_factory is None
        try:
            resumed = await resumed_runtime.restore_session(session_file)
            assert resumed.session_id == session_id
            current_receipt = resumed._build_current_coding_composition_receipt()
            assert (
                current_receipt["catalogSelectionFingerprint"]
                != historical_receipt["catalogSelectionFingerprint"]
            )
            before_prepare = session_file.read_bytes()
            await resumed.prepare_model_call_runtime()
            assert session_file.read_bytes() == before_prepare
            await resumed.session_manager.append_message(
                UserMessage(role="user", content="after resource change", timestamp=2.0)
            )
        finally:
            await resumed_runtime.dispose_session_runtime()

        restored_header, records = load_agent_transcript_file(
            session_file,
            read_only=True,
        )
        assert restored_header == header
        assert [
            record.payload.content
            for record in records
            if isinstance(record.payload, UserMessage)
        ] == ["before resource change", "after resource change"]

    asyncio.run(scenario())
