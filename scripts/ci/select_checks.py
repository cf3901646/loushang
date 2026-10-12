"""Select checks from Git changes without importing or installing the product.

The plan is shared by local development and GitHub Actions. Rules are additive;
unknown non-document paths deliberately select the full suite.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PR_ROUTING_FILES = {
    "scripts/ci/check-scopes.json",
    "scripts/ci/select_checks.py",
    "scripts/ci/verify_gate.py",
    "tests/ci/test_change_gates.py",
}
FAST_EXCLUDED_PACKAGES = {
    "plugin", "hosting", "apphost", "appservice", "appserver", "foundation",
}
FAST_RISK_CHECKS = {
    "registered_reboot", "windows_shell", "tui_native", "harness_native",
    "lsp", "install", "hosting", "apphost", "appservice",
}
E2E_PATH_PARTS = ("/session/", "/conversation/", "/transcript/")
FAST_RISK_RULE_REASONS = {"AI consumer contracts"}


def git(*args: str, root: Path = ROOT) -> bytes:
    return subprocess.check_output(["git", *args], cwd=root)


def changed_paths(base: str, head: str, *, root: Path = ROOT) -> list[str]:
    # Treat renames as delete + add, so both the old and new owners are checked.
    data = git("diff", "--name-only", "--no-renames", "-z", base, head, "--", root=root)
    return sorted({os.fsdecode(path) for path in data.split(b"\0") if path})


def local_paths(base: str, *, root: Path = ROOT) -> list[str]:
    ancestor = git("merge-base", base, "HEAD", root=root).decode().strip()
    paths = changed_paths(ancestor, "HEAD", root=root)
    for args in (
        ("diff", "--name-only", "--no-renames", "-z", "HEAD", "--"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        paths.extend(os.fsdecode(p) for p in git(*args, root=root).split(b"\0") if p)
    return sorted(set(paths))


def make_paths(root: Path = ROOT) -> dict[str, list[str]]:
    text = (root / "Makefile").read_text().replace("\\\n", " ")
    return {
        match[1]: match[2].split()
        for match in re.finditer(r"^(\w+)\s*:=\s*(.*)$", text, re.M)
    }


def select(
    paths: list[str], *, full: bool = False, pr_fast: bool = False, root: Path = ROOT
) -> dict:
    rules = json.loads((root / "scripts/ci/check-scopes.json").read_text())
    unit_inventory = json.loads((root / "scripts/ci/unit-tests.json").read_text())
    checks = {name: False for name in rules["checks"]}
    reasons: dict[str, list[str]] = {name: [] for name in checks}
    unit_packages: set[str] = set()
    e2e = False

    def enable(names: list[str], reason: str) -> None:
        for name in names:
            if name not in checks:
                raise ValueError(f"unknown check {name!r}")
            checks[name] = True
            if reason not in reasons[name]:
                reasons[name].append(reason)

    enable(["docs"], "repository documentation invariants")
    if full:
        enable(list(checks), "explicit full validation")
    variables = make_paths(root)
    for path in sorted(set(paths)):
        if path.startswith("src/") and path.endswith(".py"):
            enable(["architecture"], f"{path}: source dependency facts")
        if (
            path
            == "docs/internals/architecture/generated/current-package-dependencies.md"
        ):
            enable(["architecture"], f"{path}: generated source dependency facts")
            continue
        ordinary_document = not path.startswith("tests/") and (
            path.startswith("docs/")
            or "/" not in path
            or Path(path).name in {"README.md", "AGENTS.md", "TODO.md"}
        )
        if (path.endswith((".md", ".rst")) and ordinary_document) or path in rules[
            "document_files"
        ]:
            enable(["docs"], f"{path}: documentation")
            continue
        if pr_fast and not full and path in PR_ROUTING_FILES:
            enable(["ci"], f"{path}: PR gate routing regression and Actions syntax")
            continue
        if pr_fast and not full:
            parts = Path(path).parts
            package = None
            if len(parts) >= 4 and parts[:2] == ("src", "loushang"):
                package = parts[2]
            elif len(parts) >= 3 and parts[0] == "tests":
                package = parts[1]
            if package in unit_inventory and package not in FAST_EXCLUDED_PACKAGES:
                # Test support and newly added tests require the established
                # routing until they are explicitly classified as unit tests.
                test_is_unit = (
                    path.startswith("src/") and path.endswith(".py")
                ) or path in unit_inventory[package]
                matching_rules = [
                    rule for rule in rules["rules"]
                    if any(fnmatch.fnmatchcase(path, p) for p in rule["paths"])
                ]
                matched_checks = {
                    check
                    for rule in matching_rules
                    for check in rule["checks"]
                }
                if (
                    test_is_unit
                    and not (matched_checks & FAST_RISK_CHECKS)
                    and not (package == "coding" and "coding_ui" in matched_checks)
                    and not any(
                        rule["reason"] in FAST_RISK_RULE_REASONS
                        for rule in matching_rules
                    )
                ):
                    unit_packages.add(package)
                    e2e |= any(part in path for part in E2E_PATH_PARTS)
                    e2e |= package == "coding" and "hosted" in Path(path).name
                    continue
        matched = False
        for rule in rules["rules"]:
            if any(fnmatch.fnmatchcase(path, pattern) for pattern in rule["paths"]):
                enable(rule["checks"], f"{path}: {rule['reason']}")
                matched = True
        # Reuse the actual coverage inventories instead of copying hundreds of
        # support files into a second, drifting list of path filters.
        for name, variable_names in rules["make_scopes"].items():
            for variable in variable_names:
                if variable not in variables:
                    raise ValueError(f"missing Makefile inventory {variable}")
                if any(
                    path == p or path.startswith(p + "/") for p in variables[variable]
                ):
                    enable([name], f"{path}: {variable}")
                    matched = True
        for covered in variables["HARNESSTUI_TEST_PATHS"]:
            if path == covered or path.startswith(covered + "/"):
                scope = (
                    "coding_ui" if covered.startswith("tests/coding/") else "harnesstui"
                )
                enable([scope], f"{path}: HARNESSTUI_TEST_PATHS")
                matched = True
        if not matched:
            enable(list(checks), f"{path}: unclassified path (full validation)")

    while True:
        before = checks.copy()
        for check, dependencies in rules["check_dependencies"].items():
            if checks[check]:
                enable(dependencies, f"required by {check}")
        if before == checks:
            break
    workflows = {
        name: any(checks[check] for check in scopes)
        for name, scopes in rules["workflows"].items()
    }
    workflows["units"] = bool(unit_packages)
    workflows["e2e"] = e2e
    return {
        "version": 1,
        "paths": sorted(set(paths)),
        "checks": checks,
        "workflows": workflows,
        "unit_packages": sorted(unit_packages),
        "e2e": e2e,
        "reasons": reasons,
    }


def workflow_plan(plan: dict) -> dict:
    """Return only the plan fields consumed by downstream workflows.

    Selection reasons can repeat every changed path across many checks.  Keeping
    them in the job output makes large pull requests exceed the runner's
    per-environment-variable size limit when reusable workflows bind the plan to
    ``CI_PLAN``.  The complete plan is still printed in the selector log; jobs
    receive only the executable portion.
    """
    return {
        key: plan[key]
        for key in ("version", "paths", "checks", "workflows", "unit_packages", "e2e")
    }


def event_paths(
    event_name: str, event: dict, *, root: Path = ROOT
) -> tuple[list[str], bool]:
    if event_name in {"schedule", "workflow_dispatch"}:
        return [], True
    if event_name == "pull_request":
        pr = event["pull_request"]
        ancestor = (
            git("merge-base", pr["base"]["sha"], pr["head"]["sha"], root=root)
            .decode()
            .strip()
        )
        return changed_paths(ancestor, pr["head"]["sha"], root=root), False
    if event_name == "push":
        before, after = event["before"], event["after"]
        if before == "0" * 40:
            return [], True
        return changed_paths(before, after, root=root), False
    raise ValueError(f"unsupported event {event_name!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--head")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--pr-fast", action="store_true")
    parser.add_argument("--event", action="store_true")
    parser.add_argument("--paths", nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    full = args.full
    if args.event:
        paths, event_full = event_paths(
            os.environ["GITHUB_EVENT_NAME"],
            json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text()),
        )
        full = full or event_full
    elif args.paths is not None:
        paths = args.paths
    elif args.head:
        paths = changed_paths(args.base, args.head)
    elif full:
        paths = []
    else:
        paths = local_paths(args.base)
    plan = select(
        paths, full=full,
        pr_fast=args.pr_fast or (
            args.event and os.environ["GITHUB_EVENT_NAME"] == "pull_request"
        ),
    )
    if args.output:
        args.output.write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))
    if args.event:
        # Never put filenames in output keys or executable shell text.
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
            stream.write(
                "plan="
                + json.dumps(workflow_plan(plan), separators=(",", ":"))
                + "\n"
            )
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as stream:
            stream.write("## Selected checks\n\n")
            for check, enabled in plan["checks"].items():
                stream.write(f"- {check}: {'run' if enabled else 'not applicable'}\n")
            stream.write("\nReasons are recorded in the selection job log.\n")


if __name__ == "__main__":
    main()
