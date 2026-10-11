"""Canonical checkpoint bytes bind guarded Windows Worker reference inputs."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from loushang.coding.package_product_worker_windows_checkpoint import (
    CodingWindowsWorkerHistoryCheckpointV1,
)
from loushang.coding.package_product_worker_windows_package_references import (
    CodingWindowsWorkerPackageReferenceReviewV1,
)
from loushang.harness.resources.packages.plugin_lifecycle.records import (
    canonical_json_bytes,
)
from tests.coding.test_package_product_worker_windows_package_references import (
    _inputs,
)


def _checkpoint(tmp_path: Path) -> CodingWindowsWorkerHistoryCheckpointV1:
    prepared, semantic, quiescence, topology = _inputs(tmp_path)
    review = CodingWindowsWorkerPackageReferenceReviewV1.from_guarded_read(
        prepared, semantic, quiescence=quiescence, backup_topology=topology
    )
    return CodingWindowsWorkerHistoryCheckpointV1.from_guarded_read(
        prepared, semantic, review
    )


def test_windows_checkpoint_roundtrip_keeps_all_six_bases_and_references(
    tmp_path: Path,
) -> None:
    checkpoint = _checkpoint(tmp_path)
    assert (
        CodingWindowsWorkerHistoryCheckpointV1.from_bytes(checkpoint.to_bytes())
        == checkpoint
    )
    assert tuple(name for name, _ in checkpoint.base_digests) == (
        "optIn",
        "receipt",
        "supervisor",
        "c5",
        "launchIntent",
        "nativeProvisioning",
    )
    assert checkpoint.receipt_fingerprints
    assert checkpoint.opt_in_operation_ids
    assert checkpoint.source_snapshot.files


def test_windows_checkpoint_refuses_changed_reference_digest(tmp_path: Path) -> None:
    checkpoint = _checkpoint(tmp_path)
    with pytest.raises(ValueError, match="checkpoint is invalid"):
        replace(checkpoint, package_reference_digest="0" * 64)


def test_windows_checkpoint_refuses_noncanonical_or_unknown_bytes(
    tmp_path: Path,
) -> None:
    checkpoint = _checkpoint(tmp_path)
    document = checkpoint.to_dict()
    document["unknown"] = 1
    with pytest.raises(ValueError, match="checkpoint is invalid"):
        CodingWindowsWorkerHistoryCheckpointV1.from_bytes(
            canonical_json_bytes(document)
        )
    with pytest.raises(ValueError, match="checkpoint is invalid"):
        CodingWindowsWorkerHistoryCheckpointV1.from_bytes(
            json.dumps(checkpoint.to_dict()).encode()
        )
