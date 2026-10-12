from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path

import pytest

from loushang.coding.composition_provenance import CodingCompositionProvenanceV1
from loushang.coding.composition_sets import resolve_coding_composition_set
from loushang.coding.resume_activation_plan import (
    ActivationOwnerInputRefV1,
    ActivationOwnerSelectionRefV1,
    ResumePlanStaleError,
    build_session_activation_plan,
    require_current_resume_plan_inputs,
    require_current_resume_plan_source,
)
from loushang.coding.resume_binding import project_coding_runtime_binding_path
from loushang.coding.resume_history import (
    CodingResumeHeaderPreview,
    CodingResumeHistoryPreview,
    read_coding_resume_snapshot,
)
from loushang.coding.session_manager import SessionManager
from loushang.harness.conversation import ConversationHeader
from loushang.harness.resources.loader import ResourceLoader


def _history() -> CodingResumeHistoryPreview:
    current = resolve_coding_composition_set("coding-standard")
    return CodingResumeHistoryPreview(
        header_preview=CodingResumeHeaderPreview(
            header=ConversationHeader(
                conversation_id="session-1", version=1,
                created_at="2026-10-12T00:00:00Z",
            ),
            product_identity="coding",
            composition=CodingCompositionProvenanceV1(
                current.set_id, current.fingerprint,
            ),
        ),
        records=(), selected_records=(), selected_leaf_id=None,
        startup=None, provenance_conflict=False,
        binding_status="none", binding=None,
        selected_ancestry_digest=project_coding_runtime_binding_path(
            (), current_session_id="session-1",
        ).ancestry_digest,
        source_fingerprint="stat-v1:1:2:3:4:5",
        source_content_digest="a" * 64,
    )


def test_activation_plan_is_deterministic_and_stale_on_source_or_branch_change() -> None:
    history = _history()
    selection = ActivationOwnerSelectionRefV1(
        owner_id="resources.catalog", fingerprint="b" * 64,
        generation="generation-1",
    )
    current = resolve_coding_composition_set("coding-standard")
    first = build_session_activation_plan(
        history, current, workspace_root=Path("/workspace"),
        owner_selections=(selection,),
    )
    second = build_session_activation_plan(
        history, current, workspace_root=Path("/workspace"),
        owner_selections=(selection,),
    )

    assert first == second
    assert len(first.plan_id) == 64
    assert first.status == "needs_final_validation"
    assert first.composition_comparison.status == "same"
    require_current_resume_plan_source(first, history)
    for changed in (
        replace(history, source_fingerprint="stat-v1:changed"),
        replace(history, selected_leaf_id="another-leaf"),
        replace(history, selected_ancestry_digest="c" * 64),
        replace(history, source_content_digest="b" * 64),
    ):
        with pytest.raises(ResumePlanStaleError):
            require_current_resume_plan_source(first, changed)
    assert build_session_activation_plan(
        history, current, workspace_root=Path("/workspace"),
        owner_selections=(replace(selection, fingerprint="c" * 64),),
    ).plan_id != first.plan_id
    assert build_session_activation_plan(
        replace(history, source_content_digest="b" * 64), current,
        workspace_root=Path("/workspace"), owner_selections=(selection,),
    ).plan_id != first.plan_id


def test_activation_plan_cannot_treat_unknown_history_as_ready() -> None:
    history = replace(_history(), binding_status="unknown_version")
    plan = build_session_activation_plan(
        history, resolve_coding_composition_set("coding-standard"),
        workspace_root=Path("/workspace"),
    )
    assert plan.status == "unavailable"
    assert plan.composition_comparison.reason_codes == (
        "history.binding_unknown_version",
    )


def test_activation_plan_rejects_noncanonical_or_duplicate_owner_inputs() -> None:
    history = _history()
    current = resolve_coding_composition_set("coding-standard")
    selection = ActivationOwnerSelectionRefV1(
        owner_id="resources.catalog", fingerprint="b" * 64,
        generation="generation-1",
    )
    with pytest.raises(ValueError, match="sorted and unique"):
        build_session_activation_plan(
            history, current, workspace_root=Path("/workspace"),
            owner_selections=(selection, selection),
        )
    with pytest.raises(ValueError, match="canonical absolute"):
        build_session_activation_plan(
            history, current, workspace_root=Path("workspace"),
        )
    with pytest.raises(ValueError, match="fingerprint"):
        replace(selection, fingerprint="raw-secret")
    with pytest.raises(ValueError, match="source fingerprint"):
        build_session_activation_plan(
            replace(history, source_fingerprint="raw-secret"), current,
            workspace_root=Path("/workspace"),
        )


def test_activation_plan_rejects_rewritten_real_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from loushang.coding import resume_history as resume_history_module

    async def create() -> Path:
        manager = await SessionManager.new_with_composition(
            session_dir=tmp_path, cwd=str(tmp_path),
            composition_set="coding-standard", defer_materialization=False,
        )
        try:
            assert manager.session_file is not None
            return manager.session_file
        finally:
            await manager.dispose_runtime_profile()

    path = asyncio.run(create())
    monkeypatch.setattr(
        resume_history_module, "session_file_authority_fingerprint",
        lambda _path: "stat-v1:1:2:3:4:5",
    )
    current = resolve_coding_composition_set("coding-standard")
    original = read_coding_resume_snapshot(path, max_bytes=1024 * 1024)
    plan = build_session_activation_plan(
        original, current, workspace_root=tmp_path,
    )
    assert plan.status == "needs_final_validation"
    with path.open("ab") as stream:
        stream.write(b"\n")
    revised = read_coding_resume_snapshot(path, max_bytes=1024 * 1024)
    assert revised.source_fingerprint == original.source_fingerprint
    assert revised.source_content_digest != original.source_content_digest
    assert revised.selected_ancestry_digest == original.selected_ancestry_digest
    with pytest.raises(ResumePlanStaleError):
        require_current_resume_plan_source(plan, revised)


def test_activation_plan_references_resource_owner_input_without_retaining_receipt(
    tmp_path: Path,
) -> None:
    loader = ResourceLoader(user_resource_roots=())
    first_receipt = loader.preview_catalog_input_receipt(tmp_path)
    first_ref = ActivationOwnerInputRefV1(
        "resources.catalog", first_receipt.input_fingerprint,
    )
    current = resolve_coding_composition_set("coding-standard")
    first = build_session_activation_plan(
        _history(), current, workspace_root=tmp_path,
        owner_inputs=(first_ref,),
    )

    loader.set_runtime_options(no_skills=True)
    next_receipt = loader.preview_catalog_input_receipt(tmp_path)
    next_ref = ActivationOwnerInputRefV1(
        "resources.catalog", next_receipt.input_fingerprint,
    )
    changed = build_session_activation_plan(
        _history(), current, workspace_root=tmp_path,
        owner_inputs=(next_ref,),
    )
    assert first.plan_id != changed.plan_id
    assert first.owner_inputs == (first_ref,)
    assert "ResourceCatalogInputReceipt" not in repr(first)
    require_current_resume_plan_inputs(first, (first_ref,))
    with pytest.raises(ResumePlanStaleError, match="owner inputs changed"):
        require_current_resume_plan_inputs(first, (next_ref,))
    with pytest.raises(ResumePlanStaleError, match="owner inputs changed"):
        require_current_resume_plan_inputs(first, ())
    with pytest.raises(ResumePlanStaleError, match="owner inputs changed"):
        require_current_resume_plan_inputs(changed, (first_ref,))
