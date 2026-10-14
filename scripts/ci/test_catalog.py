"""Reviewed test roles, distinct from the historical fast-path file inventory."""
from __future__ import annotations

import json
from pathlib import Path

CATALOG_FILE = "scripts/ci/test-classification.json"
CATALOG_VERSION = 3
MODULE_CATEGORIES = {"unit", "contract"}
TARGETED_CATEGORIES = {"integration", "platform", "live", "e2e"}
TARGETED_RUNNERS = {"ubuntu-24.04", "macos-15", "windows-2022"}
MODULE_EXTRA_TESTS = {
    "ai": ["tests/protocols", "tests/examples/test_ai_examples.py",
           "tests/examples/test_auth_examples.py"],
    "agent": ["tests/examples/test_agent_examples.py"],
    "coding": ["tests/examples/test_coding_examples.py"],
    "harness": ["tests/examples/test_harness_tool_authoring_example.py",
                "tests/examples/test_harness_document_product_example.py"],
}


def load_catalog(root: Path) -> dict:
    path = root / CATALOG_FILE
    if not path.exists():
        # During incremental migration, absence retains the complete old route.
        return {"version": CATALOG_VERSION, "modules": {}}
    catalog = json.loads(path.read_text())
    if (not isinstance(catalog, dict)
            or catalog.get("version") != CATALOG_VERSION
            or not isinstance(catalog.get("modules"), dict)):
        raise ValueError("invalid test classification catalog")
    for module, entry in catalog["modules"].items():
        if not module.isidentifier() or not isinstance(entry, dict) or entry.get("complete") is not True:
            raise ValueError(f"unreviewed classified module: {module}")
        files = entry.get("files")
        if not isinstance(files, dict) or not files:
            raise ValueError(f"empty classified module: {module}")
        discovered = {p.relative_to(root).as_posix()
                      for p in (root / "tests" / module).rglob("test_*.py")}
        for extra in MODULE_EXTRA_TESTS.get(module, []):
            extra_path = root / extra
            if not extra_path.exists():
                raise ValueError(f"missing module regression path {extra!r}")
            if extra_path.is_dir():
                discovered.update(p.relative_to(root).as_posix()
                                  for p in extra_path.rglob("test_*.py"))
            else:
                discovered.add(extra)
        if set(files) != discovered:
            raise ValueError(f"test classification incomplete for {module}: "
                             f"missing={sorted(discovered - set(files))}, "
                             f"stale={sorted(set(files) - discovered)}")
        for file, role in files.items():
            if (not isinstance(role, dict)
                    or role.get("category") not in MODULE_CATEGORIES | TARGETED_CATEGORIES
                    or not isinstance(role.get("assertion"), str)
                    or not role["assertion"].strip()):
                raise ValueError(f"invalid reviewed test role: {file}")
            _validate_platforms(file, role)
        if not any(role["category"] in MODULE_CATEGORIES for role in files.values()):
            raise ValueError(f"classified module has no unit or contract tests: {module}")
        fixtures = entry.get("fixtures", {})
        if not isinstance(fixtures, dict):
            raise ValueError(f"invalid fixture inventory: {module}")
        for fixture, role in fixtures.items():
            if (not fixture.startswith(f"tests/{module}/")
                    or ".." in Path(fixture).parts or fixture in files
                    or not (root / fixture).is_file()):
                raise ValueError(f"invalid or missing dedicated fixture: {fixture}")
            if (not isinstance(role, dict)
                    or role.get("category") not in MODULE_CATEGORIES | TARGETED_CATEGORIES
                    or not isinstance(role.get("assertion"), str) or not role["assertion"].strip()):
                raise ValueError(f"invalid dedicated fixture role: {fixture}")
            _validate_platforms(fixture, role)
            consumers = role.get("consumers")
            if (not isinstance(consumers, list) or not consumers
                    or not all(isinstance(consumer, str) for consumer in consumers)
                    or len(set(consumers)) != len(consumers)
                    or set(consumers) - set(files)):
                raise ValueError(f"unreviewed dedicated fixture consumers: {fixture}")
    return catalog


def module_unit_paths(module: str, *, root: Path) -> list[str] | None:
    entry = load_catalog(root)["modules"].get(module)
    return sorted(
        path for path, role in entry["files"].items()
        if role["category"] in MODULE_CATEGORIES
    ) if entry else None


def reviewed_unit_owner(path: str, *, catalog: dict) -> str | None:
    for module, entry in catalog["modules"].items():
        reviewed_file = entry["files"].get(path)
        if (
            reviewed_file is not None
            and reviewed_file["category"] in MODULE_CATEGORIES
        ) or (
            path in entry.get("fixtures", {})
            and entry["fixtures"][path]["category"] in MODULE_CATEGORIES
        ):
            return module
    return None


def targeted_test_cases(path: str, *, catalog: dict) -> list[tuple[str, dict]]:
    """Return directly runnable reviewed tests affected by a targeted change."""
    cases: list[tuple[str, dict]] = []
    for entry in catalog["modules"].values():
        role = entry["files"].get(path)
        if role is not None and role["category"] in TARGETED_CATEGORIES - {"live"}:
            cases.append((path, role))
        fixture = entry.get("fixtures", {}).get(path)
        if fixture is None or fixture["category"] not in TARGETED_CATEGORIES - {"live"}:
            continue
        for consumer in fixture["consumers"]:
            consumer_role = entry["files"][consumer]
            if consumer_role["category"] not in TARGETED_CATEGORIES - {"live"}:
                raise ValueError(f"targeted fixture has non-targeted consumer: {path}")
            cases.append((consumer, consumer_role))
    return cases


def _validate_platforms(path: str, role: dict) -> None:
    category = role["category"]
    platforms = role.get("platforms")
    if category in TARGETED_CATEGORIES - {"live"}:
        if (not isinstance(platforms, list) or not platforms
                or not all(isinstance(platform, str) for platform in platforms)
                or len(platforms) != len(set(platforms))
                or set(platforms) - TARGETED_RUNNERS):
            raise ValueError(f"invalid targeted test platforms: {path}")
    elif platforms is not None:
        raise ValueError(f"non-targeted test declares platforms: {path}")
