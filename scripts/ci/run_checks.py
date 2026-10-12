"""Local and CI commands for the inexpensive, independently selectable scopes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from select_checks import ROOT, make_paths

OFFLINE_MARKERS = (
    "not live and not requires_host_runtime and not tui_render_contract "
    "and not tui_terminal_backend and not tui_terminal_contract and not tui_tmux_integration"
)
MODULE_EXTRA_TESTS = {
    "ai": ["tests/protocols", "tests/examples/test_ai_examples.py",
           "tests/examples/test_auth_examples.py"],
    "agent": ["tests/examples/test_agent_examples.py"],
    "coding": ["tests/examples/test_coding_examples.py"],
    "harness": ["tests/examples/test_harness_tool_authoring_example.py",
                "tests/examples/test_harness_document_product_example.py"],
}


def commands(
    scope: str, *, root: Path = ROOT, plan: dict | None = None,
    shard: int = 0, shards: int = 1,
) -> list[list[str]]:
    if shards < 1 or not 0 <= shard < shards:
        raise ValueError(f"invalid regression shard {shard}/{shards}")
    if scope != "coding" and not scope.startswith("unit_") and (shard != 0 or shards != 1):
        raise ValueError("shards are only supported for module regression")
    python = sys.executable
    pytest = [python, "scripts/dev/run_pytest.py"]
    inventories = make_paths(root)
    coding_ui_paths = sorted(
        {
            path
            for name in ("HARNESSTUI_TEST_PATHS", "CODING_TUI_PRODUCT_TEST_PATHS")
            for path in inventories[name]
            if path.startswith("tests/coding/")
        }
    )
    coding_ignores = [f"--ignore={path}" for path in coding_ui_paths]
    if scope.startswith("unit_"):
        package = scope.removeprefix("unit_")
        unit_paths = json.loads((root / "scripts/ci/unit-tests.json").read_text())
        if package not in unit_paths:
            raise ValueError(f"unknown unit package {package!r}")
        package_dir = root / "tests" / package
        paths = [f"tests/{package}"] if package_dir.is_dir() else unit_paths[package]
        extras = MODULE_EXTRA_TESTS.get(package, [])
        for path in extras:
            if not (root / path).exists():
                raise ValueError(f"missing module regression path {path!r}")
        shard_args = (
            ["-p", "pytest_shard", "--ci-shard-index", str(shard),
             "--ci-shard-count", str(shards)]
            if shards > 1 else []
        )
        return [
            pytest
            + (coding_ignores if package == "coding" else [])
            + paths + extras
            + ["-m", f"{OFFLINE_MARKERS} and not e2e_smoke",
               "--skip-host-runtime", "--strict-markers", "-q", *shard_args]
        ]
    if scope == "e2e_smoke":
        return [
            pytest
            + [
                "tests/coding/test_hosted_application.py::"
                "test_G12_VERTICAL_CANARY_crosses_real_composition_create_turn_resume_close",
                "-m", "e2e_smoke and not live", "--strict-markers", "-q",
            ]
        ]
    if scope == "host_runtime" and plan is not None:
        packages = (
            "coding",
            "harness",
            "hosting",
            "apphost",
            "appservice",
            "agent",
            "foundation",
        )
        paths = [f"tests/{package}" for package in packages if plan["checks"][package]]
        if plan["checks"]["appservice"]:
            paths.append("tests/appserver")
        if not paths:
            raise ValueError("host-runtime selection has no owning package")
        if all(plan["checks"].values()):
            paths = ["tests"]
        elif plan["checks"]["coding"]:
            paths += coding_ignores
        return [pytest + paths + ["-m", "requires_host_runtime and not live", "-q"]]
    if scope in {"agent", "coding", "foundation"}:
        # Existing packages do not all have established package-wide mypy/lint
        # baselines. Start with their offline regression suites, without inventing
        # new lint thresholds as part of CI routing.
        shard_args = (
            ["-p", "pytest_shard", "--ci-shard-index", str(shard),
             "--ci-shard-count", str(shards)]
            if shards > 1 else []
        )
        return [pytest + (coding_ignores if scope == "coding" else [])
                + [f"tests/{scope}", "-m", OFFLINE_MARKERS,
                   "--skip-host-runtime", "-q", *shard_args]]
    if scope == "tui_unit":
        return [
            pytest + ["tests/tui", "-m", OFFLINE_MARKERS, "--skip-host-runtime", "-q"]
        ]
    if scope in {"harnesstui", "coding_ui"}:
        all_tests = (
            inventories["HARNESSTUI_TEST_PATHS"]
            + inventories["CODING_TUI_PRODUCT_TEST_PATHS"]
        )
        coding = scope == "coding_ui"
        tests = [
            path for path in all_tests if path.startswith("tests/coding/") == coding
        ]
        source_vars = (
            [
                "HARNESSTUI_CODING_ADAPTERS",
                "CODING_TUI_PRODUCT_SOURCES",
                "HARNESSTUI_TEST_SUPPORT",
            ]
            if coding
            else ["HARNESSTUI_SHARED_SOURCES"]
        )
        sources = [path for name in source_vars for path in inventories[name]]
        typed = [path for path in sources if not path.startswith("tests/")]
        return [
            [python, "-m", "ruff", "check", *sources, *tests],
            [python, "-m", "mypy", "--follow-imports=silent", *typed],
            pytest + tests + ["-m", "not tui_render_contract", "-q"],
        ]
    if scope == "docs":
        return [
            [python, "scripts/ci/check_docs.py", "--plan", ".artifacts/check-plan.json"]
        ]
    if scope == "architecture":
        return [
            [
                python,
                "scripts/architecture/render_current_package_dependencies.py",
                "--check",
            ]
        ]
    if scope == "ci":
        return [[python, "-m", "unittest", "discover", "-s", "tests/ci", "-v"]]
    targets = {
        "ai": "check-ai",
        "harness": "check-harness",
        "hosting": "check-hosting",
        "apphost": "check-apphost",
        "appservice": "check-appservice",
        "tui_playback": "test-tui-render-contract",
    }
    if scope in targets:
        return [["make", targets[scope]]]
    raise ValueError(f"scope {scope!r} requires its platform-specific workflow")


def run(scope: str, *, plan: dict | None = None, shard: int = 0, shards: int = 1) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(ROOT / "src"), str(ROOT / "scripts" / "ci"),
                          env.get("PYTHONPATH")) if part
    )
    for command in commands(scope, plan=plan, shard=shard, shards=shards):
        print("Running:", " ".join(command), flush=True)
        completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
        if (
            scope == "host_runtime"
            and plan is not None
            and not all(plan["checks"].values())
            and completed.returncode == 5
        ):
            # A scoped package may have no tests with this opt-in marker.
            print("No host-runtime cases selected in the scoped packages.", flush=True)
            continue
        completed.check_returncode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope")
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    args = parser.parse_args()
    # Unit/package jobs must not accidentally activate opt-in provider tests.
    os.environ.pop("LOUSHANG_AI_LIVE", None)
    plan = json.loads(os.environ["CI_PLAN"]) if "CI_PLAN" in os.environ else None
    run(args.scope, plan=plan, shard=args.shard, shards=args.shards)


if __name__ == "__main__":
    main()
