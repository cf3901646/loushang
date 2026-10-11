"""A Windows Worker history preparation binds exact source and semantic reads."""

from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256

import pytest

from loushang.coding.package_product_worker_windows_history_preparation import (
    CodingWindowsWorkerHistoryPreparationV1,
)
from loushang.coding.package_product_worker_windows_history_sources import (
    CodingWindowsWorkerHistorySemanticReadV1,
    CodingWindowsWorkerHistorySourceFileV1,
    CodingWindowsWorkerHistorySourceSnapshotV1,
)
from loushang.coding.package_product_worker_windows_provisioning_journal import (
    WindowsWorkerProvisioningAttemptV1,
    _Record,
)
from loushang.coding.package_product_worker_windows_recovery_inventory import (
    CodingWindowsWorkerOfflineRecoverySnapshotV1,
)
from loushang.harness.worker.activation_state_journal import _StateRecord
from loushang.harness.worker.product_activation import _initial_state


def _semantic_read() -> CodingWindowsWorkerHistorySemanticReadV1:
    source = CodingWindowsWorkerHistorySourceSnapshotV1.create(
        scope_id="scope-a",
        store_id="store-a",
        lease_owner_revision=2,
        files=(
            CodingWindowsWorkerHistorySourceFileV1(
                name="worker-opt-in.jsonl",
                size=3,
                sha256_digest=sha256(b"abc").hexdigest(),
            ),
        ),
    )
    recovery = CodingWindowsWorkerOfflineRecoverySnapshotV1(
        store_id="store-a",
        lease_owner_revision=2,
        attempts=(),
        opt_in_decisions=(),
        receipt_records=(),
        supervisor_records=(),
        activation_state_owner_present=False,
        activation_state_revision=0,
        retained_activation_attempts=(),
        native_job_absence=(),
        gc_reservation_revision=3,
        gc_revision_refs=frozenset(),
        worker_backup_observations=(),
    )
    return CodingWindowsWorkerHistorySemanticReadV1(
        source_snapshot=source, offline_recovery=recovery
    )


def test_windows_worker_history_preparation_replays_only_exact_semantics() -> None:
    semantic = _semantic_read()
    prepared = CodingWindowsWorkerHistoryPreparationV1.create(semantic)
    assert (
        CodingWindowsWorkerHistoryPreparationV1.from_bytes(prepared.to_bytes())
        == prepared
    )
    prepared.require_semantic_read(semantic)
    with pytest.raises(ValueError, match="semantic read changed"):
        prepared.require_semantic_read(
            replace(
                semantic,
                offline_recovery=replace(
                    semantic.offline_recovery, gc_reservation_revision=4
                ),
            )
        )


def test_windows_worker_history_preparation_rejects_changed_bytes() -> None:
    prepared = CodingWindowsWorkerHistoryPreparationV1.create(_semantic_read())
    document = json.loads(prepared.to_bytes())
    document["semanticDigest"] = sha256(b"other semantics").hexdigest()
    with pytest.raises(ValueError, match="preparation is invalid"):
        CodingWindowsWorkerHistoryPreparationV1.from_bytes(
            json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
        )
    with pytest.raises(ValueError, match="preparation is invalid"):
        CodingWindowsWorkerHistoryPreparationV1.from_bytes(prepared.to_bytes() + b" ")


def test_windows_worker_history_preparation_binds_complete_c5_state() -> None:
    semantic = _semantic_read()
    prepared = CodingWindowsWorkerHistoryPreparationV1.create(semantic)
    changed = replace(
        semantic,
        offline_recovery=replace(
            semantic.offline_recovery,
            activation_state_records=(
                _StateRecord.create(_initial_state(restart_budget=3)),
            ),
        ),
    )
    with pytest.raises(ValueError, match="semantic read changed"):
        prepared.require_semantic_read(changed)


def test_windows_worker_history_preparation_binds_native_records() -> None:
    semantic = _semantic_read()
    prepared = CodingWindowsWorkerHistoryPreparationV1.create(semantic)
    record = _Record(
        revision=1,
        document={"stateRevision": 1},
        digest=sha256(b"native record").hexdigest(),
    )
    changed = replace(
        semantic,
        offline_recovery=replace(
            semantic.offline_recovery,
            native_provisioning_attempts=(
                WindowsWorkerProvisioningAttemptV1(
                    attempt_id="a" * 32,
                    phase="reserved",
                    state_revision=1,
                    identity={},
                    phase_history=("reserved",),
                    witness_present_history=(False,),
                    last_witness_state=None,
                    settlement_fingerprint=None,
                    records=(record,),
                ),
            ),
        ),
    )
    with pytest.raises(ValueError, match="semantic read changed"):
        prepared.require_semantic_read(changed)
