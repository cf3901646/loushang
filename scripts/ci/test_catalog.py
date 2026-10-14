"""Reviewed test roles, distinct from the historical fast-path file inventory."""
from __future__ import annotations

import json
from pathlib import Path

CATALOG_FILE = "scripts/ci/test-classification.json"
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
        return {"version": 1, "modules": {}}
    catalog = json.loads(path.read_text())
    if not isinstance(catalog, dict) or catalog.get("version") != 1 or not isinstance(catalog.get("modules"), dict):
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
            if not isinstance(role, dict) or role.get("category") not in {"unit", "contract"} or not isinstance(role.get("assertion"), str) or not role["assertion"].strip():
                raise ValueError(f"invalid reviewed test role: {file}")
    return catalog


def module_unit_paths(module: str, *, root: Path) -> list[str] | None:
    entry = load_catalog(root)["modules"].get(module)
    return sorted(entry["files"]) if entry else None


def reviewed_unit_owner(path: str, *, catalog: dict) -> str | None:
    for module, entry in catalog["modules"].items():
        if path in entry["files"]:
            return module
    return None
