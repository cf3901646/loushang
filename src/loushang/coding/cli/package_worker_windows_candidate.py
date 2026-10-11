"""Explicit Windows Worker candidate management and offline recovery."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import secrets
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from loushang.coding._plugin_lifecycle import (
    CodingPluginLifecycleStateLayout,
    resolve_coding_plugin_lifecycle_state_layout,
)
from loushang.coding.package_product_runtime import (
    CODING_PACKAGE_PRODUCT_RUNTIME_PROTOCOL_EPOCH,
    admit_coding_external_worker_wheel,
    open_coding_fenced_product_application_owner,
)
from loushang.coding.package_product_worker_windows_activation_state_journal import (
    CodingWindowsWorkerActivationStateJournal,
)
from loushang.coding.package_product_worker_windows_backend_release import (
    review_coding_windows_worker_backend_release,
)
from loushang.coding.package_product_worker_windows_crash_recovery import (
    recover_coding_windows_product_worker_crash_attempt,
)
from loushang.coding.package_product_worker_windows_installed_backend import (
    install_coding_windows_worker_backend_release,
)
from loushang.coding.package_product_worker_windows_native_approval_owner import (
    CodingWindowsWorkerNativeApprovalOwner,
)
from loushang.coding.package_product_worker_windows_opt_in_owner import (
    CodingWindowsWorkerProductOptInOwner,
)
from loushang.coding.package_product_worker_windows_orphan_review import (
    review_coding_windows_product_worker_orphan_runtime,
)
from loushang.harness.package_product.product_local_wheel_runtime import (
    WindowsLocalWheelProductSessionOwner,
)
from loushang.harness.package_product.product_runtime import (
    PackageProductRuntimeRequestV1,
)
from loushang.harness.plugin_management.operations import PluginManagementCommandV1
from loushang.harness.plugin_management.records import PluginDesiredStateMutationV1
from loushang.harness.resources.packages.plugin_lifecycle.windows_quarantine import (
    open_windows_directory,
    open_windows_regular_file_at,
)
from loushang.harness.resources.packages.product_contract import (
    PackageProductLifecycleIntentV1,
)
from loushang.harness.resources.packages.product_local_wheel_policy import (
    PackageProductLocalWorkerAdmissionV1,
)

_SAFE_ERROR_CODE = re.compile(r"[a-z][a-z0-9_]{1,127}\Z")
_MAX_WHEEL_BYTES = 64 * 1024 * 1024


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="loushang-worker-windows-candidate")
    parser.add_argument("--workspace", required=True, help="fenced Coding workspace")
    parser.add_argument(
        "--windows-candidate", action="store_true", help=argparse.SUPPRESS
    )
    actions = parser.add_subparsers(dest="action", required=True)
    for action, help_text in (
        ("inspect", "inspect one retained Worker attempt"),
        ("recover-crash", "resume exact Product crash cleanup and C5 settlement"),
    ):
        command = actions.add_parser(action, help=help_text)
        command.add_argument("--attempt-id", required=True)
    capture = actions.add_parser(
        "candidate-capture", help="capture one inert Worker Wheel"
    )
    capture.add_argument("--wheel", required=True)
    capture.add_argument("--contribution-id", required=True)
    capture.add_argument("--owner-id", required=True)
    install_candidate = actions.add_parser(
        "candidate-install", help="install one captured Worker disabled"
    )
    install_candidate.add_argument("--plugin-id", required=True)
    install_candidate.add_argument("--artifact-digest", required=True)
    install_candidate.add_argument("--operation-id", required=True)
    enable_candidate = actions.add_parser(
        "candidate-enable", help="enable one exact installed Worker"
    )
    enable_candidate.add_argument("--plugin-id", required=True)
    enable_candidate.add_argument("--artifact-digest", required=True)
    enable_candidate.add_argument("--operation-id", required=True)
    enable_candidate.add_argument(
        "--expected-inventory-revision", type=int, required=True
    )
    actions.add_parser("release-status", help="read the exact native approval")
    review = actions.add_parser(
        "release-review", help="review the installed backend Wheel"
    )
    review.add_argument("--wheel", required=True)
    approve = actions.add_parser("release-approve", help="approve one exact review")
    approve.add_argument("--wheel", required=True)
    approve.add_argument("--review-id", required=True)
    approve.add_argument("--operation-id", required=True)
    approve.add_argument("--expected-generation", type=int, required=True)
    install_release = actions.add_parser(
        "release-install", help="install the approved backend"
    )
    install_release.add_argument("--wheel", required=True)
    install_release.add_argument("--review-id", required=True)
    revoke_release = actions.add_parser("release-revoke", help="revoke native approval")
    revoke_release.add_argument("--operation-id", required=True)
    revoke_release.add_argument("--expected-generation", type=int, required=True)
    status = actions.add_parser("candidate-status", help="read one Worker opt-in")
    status.add_argument("--plugin-id", required=True)
    allow = actions.add_parser("candidate-allow", help="allow one selected Worker")
    allow.add_argument("--plugin-id", required=True)
    allow.add_argument("--operation-id", required=True)
    allow.add_argument("--expected-generation", type=int, required=True)
    allow.add_argument("--require-worker", action="store_true")
    revoke = actions.add_parser("candidate-revoke", help="revoke one Worker opt-in")
    revoke.add_argument("--plugin-id", required=True)
    revoke.add_argument("--operation-id", required=True)
    revoke.add_argument("--expected-generation", type=int, required=True)
    args = parser.parse_args(argv)
    if (
        os.name != "nt"
        or platform.machine().lower() not in {"x86_64", "amd64"}
        or not args.windows_candidate
    ):
        sys.stderr.write(
            "Windows Worker candidate refused: windows_worker_candidate_platform_closed\n"
        )
        return 1
    try:
        workspace = Path(args.workspace).expanduser().resolve(strict=True)
        if not workspace.is_dir():
            raise ValueError("Coding workspace must be a directory")
        lifecycle = resolve_coding_plugin_lifecycle_state_layout(workspace)
        if args.action == "candidate-capture":
            binding = admit_coding_external_worker_wheel(
                lifecycle,
                source=Path(args.wheel).expanduser().absolute(),
                admission=PackageProductLocalWorkerAdmissionV1(
                    contribution_id=args.contribution_id,
                    owner_id=args.owner_id,
                    native_platform="windows-amd64",
                ),
            )
            document = {
                "workerCandidateBinding": binding.to_dict(),
                "productAdmission": "not_checked",
                "productUse": "not_checked",
            }
        else:
            document = _run_product_action(lifecycle, workspace, args)
    except (OSError, RuntimeError, ValueError, PackageNotFoundError) as error:
        reason = getattr(error, "code", None)
        if not isinstance(reason, str) or _SAFE_ERROR_CODE.fullmatch(reason) is None:
            reason = "windows_worker_candidate_recovery_unavailable"
        sys.stderr.write(f"Windows Worker candidate refused: {reason}\n")
        return 1
    sys.stdout.write(json.dumps(document, sort_keys=True) + "\n")
    return 0


def _run_product_action(
    lifecycle: CodingPluginLifecycleStateLayout,
    workspace: Path,
    args: argparse.Namespace,
) -> dict[str, object]:
    owner = open_coding_fenced_product_application_owner(
        lifecycle,
        workspace=workspace,
        runtime_version=version("loushang"),
        runtime_protocol_epoch=CODING_PACKAGE_PRODUCT_RUNTIME_PROTOCOL_EPOCH,
        windows_candidate=True,
        worker_candidates=True,
    )
    try:
        product = owner.runtime_owner.product_owner
        if type(product) is not WindowsLocalWheelProductSessionOwner:
            raise ValueError("Windows Worker candidate Product is unavailable")
        if args.action == "inspect":
            review = review_coding_windows_product_worker_orphan_runtime(
                product, attempt_id=args.attempt_id
            )
            attempt = review.attempt
            if attempt is None:
                raise ValueError("Windows Worker attempt is absent")
            c5 = tuple(
                item
                for item in CodingWindowsWorkerActivationStateJournal(
                    product
                ).retained_attempts_read_only()
                if item.attempt_id == args.attempt_id
            )
            document = {
                "attemptId": args.attempt_id,
                "supervisorPhase": attempt.supervisor_phase,
                "nativePhase": attempt.native_phase,
                "nativeJobAbsent": review.native_job_absent,
                "orphanLeaseCount": len(review.orphan_leases),
                "payloadRetained": attempt.payload_directory_identity is not None,
                "c5Phase": c5[0].phase if len(c5) == 1 else None,
            }
        elif args.action == "recover-crash":
            settled = recover_coding_windows_product_worker_crash_attempt(
                product, attempt_id=args.attempt_id
            )
            document = {
                "attemptId": settled.attempt_id,
                "c5Phase": settled.phase,
                "c5Revision": settled.last_seen_revision,
            }
        else:
            document = _execute(product, args)
    finally:
        owner.close()
    return document


def _execute(
    product: WindowsLocalWheelProductSessionOwner, args: argparse.Namespace
) -> dict[str, object]:
    if args.action == "release-status":
        decision = CodingWindowsWorkerNativeApprovalOwner(product).current()
        return {"approvalDecision": None if decision is None else decision.to_dict()}
    if args.action == "release-revoke":
        decision = CodingWindowsWorkerNativeApprovalOwner(product).revoke(
            operation_id=args.operation_id,
            expected_generation=args.expected_generation,
        )
        return {"approvalDecision": decision.to_dict()}
    if args.action in {"release-review", "release-approve", "release-install"}:
        wheel = _read_wheel(Path(args.wheel))
        review = review_coding_windows_worker_backend_release(
            product, loushang_wheel=wheel
        )
        if args.action == "release-review":
            return {"nativeReleaseReview": review.to_dict()}
        if args.review_id != review.review_id:
            raise ValueError("Windows Worker backend review changed")
        if args.action == "release-approve":
            decision = CodingWindowsWorkerNativeApprovalOwner(product).approve(
                loushang_wheel=wheel,
                review_id=args.review_id,
                operation_id=args.operation_id,
                expected_generation=args.expected_generation,
            )
            return {"approvalDecision": decision.to_dict()}
        installed = install_coding_windows_worker_backend_release(
            product, loushang_wheel=wheel, review_id=args.review_id
        )
        return {
            "nativeClosure": installed.native_closure().to_dict(),
            "approvalGeneration": installed.approval_generation,
        }
    if args.action in {"candidate-status", "candidate-allow", "candidate-revoke"}:
        opt_in = CodingWindowsWorkerProductOptInOwner(product)
        if args.action == "candidate-status":
            decision = opt_in.current(args.plugin_id)
        elif args.action == "candidate-allow":
            decision = opt_in.allow(
                plugin_id=args.plugin_id,
                operation_id=args.operation_id,
                expected_generation=args.expected_generation,
                require_worker=args.require_worker,
            )
        else:
            decision = opt_in.revoke(
                plugin_id=args.plugin_id,
                operation_id=args.operation_id,
                expected_generation=args.expected_generation,
            )
        return {
            "candidateOptInDecision": None if decision is None else decision.to_dict(),
            "defaultSessionRouting": "closed",
        }
    if args.action in {"candidate-install", "candidate-enable"}:
        matching = tuple(
            binding
            for binding in product.policy.bindings
            if binding.source_trust_class == "local-worker-candidate"
            and binding.plugin_id == args.plugin_id
            and binding.artifact_digest == args.artifact_digest
        )
        if len(matching) != 1:
            raise ValueError("Windows Worker candidate is unavailable or ambiguous")
        binding = matching[0]
        snapshot = product.desired_state.snapshot()
        installed = tuple(
            item
            for item in snapshot.installations
            if item.installation_key.plugin_id == args.plugin_id
            and item.installation_key.product_id == "coding"
            and item.installation_key.installation_scope == "workspace"
        )
        if len(installed) > 1:
            raise ValueError("Windows Worker candidate installation is ambiguous")
        if args.action == "candidate-enable":
            if len(installed) != 1 or installed[0].selection.package_revision is None:
                raise ValueError("Windows Worker candidate is not installed")
            revision = installed[0].selection.package_revision
            if (
                revision.package_source_identity != binding.source_identity
                or revision.package_content_digest != binding.artifact_digest
            ):
                raise ValueError("Windows Worker candidate selection changed")
            operation = product.management.submit(
                PluginManagementCommandV1(
                    action="enable",
                    mutation=PluginDesiredStateMutationV1(
                        operation_id=args.operation_id,
                        idempotency_key=args.operation_id,
                        expected_inventory_revision=args.expected_inventory_revision,
                        installation_key=installed[0].installation_key,
                        desired_state="installed_enabled",
                        package_revision=None,
                        actor_id=product.actor_id,
                        policy_revision=product.desired_policy_revision,
                    ),
                )
            )
            if (
                operation.status != "terminal"
                or operation.result is None
                or operation.result.disposition != "succeeded"
            ):
                raise ValueError("Windows Worker candidate enable did not settle")
            return {
                "candidateManagementOperation": operation.to_dict(),
                "inventoryRevision": product.desired_state.snapshot().inventory_revision,
            }
        if installed:
            revision = installed[0].selection.package_revision
            if (
                revision is None
                or revision.package_source_identity != binding.source_identity
                or revision.package_content_digest != binding.artifact_digest
            ):
                raise ValueError("Windows Worker candidate installation changed")
            return {
                "candidateInstall": {
                    "pluginId": args.plugin_id,
                    "artifactDigest": args.artifact_digest,
                    "alreadyInstalled": True,
                    "inventoryRevision": snapshot.inventory_revision,
                }
            }
        session_id = f"worker-candidate-install-{secrets.token_hex(16)}"
        factory = product.factory_for_session(
            session_id=session_id, cwd=product.workspace, runtime_id=session_id
        )
        try:
            runtime = factory.create(
                PackageProductRuntimeRequestV1(
                    product_id="coding",
                    session_id=session_id,
                    cwd=str(product.workspace),
                )
            )
        except BaseException:
            factory.dispose_unbound_runtime()
            raise
        try:
            runtime.activate()
            routed = runtime.lifecycle.route(
                PackageProductLifecycleIntentV1(
                    operation_id=args.operation_id,
                    action="install",
                    source=binding.source_identity,
                    scope="project",
                ),
                entrypoint="cli",
            )
            if (
                not routed.handled
                or routed.record is None
                or routed.record.lifecycle != "installed"
            ):
                raise ValueError("Windows Worker candidate install did not settle")
            selected = tuple(
                item
                for item in product.desired_state.snapshot().installations
                if item.installation_key.plugin_id == args.plugin_id
                and item.installation_key.product_id == "coding"
                and item.installation_key.installation_scope == "workspace"
            )
            if (
                len(selected) != 1
                or selected[0].selection.package_revision is None
                or selected[0].selection.package_revision.package_source_identity
                != binding.source_identity
                or selected[0].selection.package_revision.package_content_digest
                != binding.artifact_digest
            ):
                raise ValueError("Windows Worker candidate install selection changed")
            return {
                "candidateInstall": {
                    "pluginId": args.plugin_id,
                    "artifactDigest": args.artifact_digest,
                    "alreadyInstalled": False,
                    "inventoryRevision": product.desired_state.snapshot().inventory_revision,
                }
            }
        finally:
            runtime.dispose_runtime()
    raise ValueError("Windows Worker candidate action is unsupported")


def _read_wheel(path: Path) -> bytes:
    target = path.expanduser().absolute()
    parent = open_windows_directory(target.parent, writable=False)
    try:
        descriptor = open_windows_regular_file_at(
            parent, target.name, create_new=False, write=False
        )
        try:
            metadata = os.fstat(descriptor)
            if not 0 < metadata.st_size <= _MAX_WHEEL_BYTES:
                raise ValueError("Windows Worker backend Wheel source is invalid")
            chunks: list[bytes] = []
            size = 0
            while True:
                chunk = os.read(descriptor, min(64 * 1024, _MAX_WHEEL_BYTES + 1 - size))
                if not chunk:
                    break
                size += len(chunk)
                if size > _MAX_WHEEL_BYTES:
                    raise ValueError("Windows Worker backend Wheel exceeds its bound")
                chunks.append(chunk)
            if size != metadata.st_size:
                raise ValueError("Windows Worker backend Wheel changed during read")
            return b"".join(chunks)
        finally:
            os.close(descriptor)
    finally:
        os.close(parent)


if __name__ == "__main__":
    raise SystemExit(main())
