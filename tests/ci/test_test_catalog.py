from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/ci"))

commands = importlib.import_module("run_checks").commands
select = importlib.import_module("select_checks").select
catalog_module = importlib.import_module("test_catalog")
load_catalog = catalog_module.load_catalog
module_unit_paths = catalog_module.module_unit_paths


class CatalogTests(unittest.TestCase):
    def test_reviewed_modules_cover_their_complete_current_test_directories(self):
        catalog = load_catalog(ROOT)
        self.assertEqual(set(catalog["modules"]), {"channel", "resource", "work"})
        for module, entry in catalog["modules"].items():
            self.assertEqual(set(entry["files"]), {
                p.relative_to(ROOT).as_posix()
                for p in (ROOT / "tests" / module).rglob("test_*.py")
            })

    def test_pure_test_changes_do_not_schedule_product_integration_or_e2e(self):
        for path in ("tests/resource/test_frontmatter.py", "tests/channel/test_host.py",
                     "tests/channel/test_session_work_adapter.py", "tests/work/test_runtime.py",
                     "tests/work/test_event_log.py"):
            with self.subTest(path=path):
                plan = select([path], root=ROOT, pr_fast=True)
                self.assertFalse(plan["e2e"])
                self.assertEqual([k for k, enabled in plan["checks"].items() if enabled], ["docs"])
                self.assertEqual([k for k, enabled in plan["workflows"].items() if enabled], ["units"])

    def test_mixed_source_test_and_shared_fixture_changes_keep_necessary_coverage(self):
        test = "tests/resource/test_frontmatter.py"
        for change in ("src/loushang/resource/frontmatter.py", "tests/conftest.py",
                       "tests/coding/test_pr_smoke.py"):
            with self.subTest(change=change):
                self.assertTrue(select([test, change], root=ROOT, pr_fast=True)["e2e"])
        unknown = select(["tests/coding/test_new_integration.py"], root=ROOT, pr_fast=True)
        self.assertTrue(unknown["e2e"])

    def test_classified_module_runner_has_static_checks_and_full_reviewed_set(self):
        for module in ("channel", "resource", "work"):
            planned = commands(f"unit_{module}", root=ROOT)
            self.assertEqual(len(planned), 2)
            self.assertIn("ruff", planned[0])
            for path in module_unit_paths(module, root=ROOT):
                self.assertIn(path, planned[1])
            self.assertIn("--skip-host-runtime", planned[1])
            self.assertIn("--strict-markers", planned[1])
            self.assertIn("not live", planned[1][planned[1].index("-m") + 1])

    def test_new_unclassified_file_and_deleted_stale_file_fail_classification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts/ci").mkdir(parents=True)
            (root / "tests/demo").mkdir(parents=True)
            file = root / "tests/demo/test_one.py"
            file.write_text("def test_one(): pass\n")
            catalog = {"version": 1, "modules": {"demo": {
                "complete": True, "files": {"tests/demo/test_one.py": {
                    "category": "unit", "assertion": "one behavior"}}}}}
            (root / "scripts/ci/test-classification.json").write_text(json.dumps(catalog))
            self.assertIsNotNone(module_unit_paths("demo", root=root))
            extra = root / "tests/demo/test_new.py"
            extra.write_text("def test_new(): pass\n")
            with self.assertRaisesRegex(ValueError, "missing=.*test_new"):
                load_catalog(root)
            extra.unlink()
            file.unlink()
            with self.assertRaisesRegex(ValueError, "stale=.*test_one"):
                load_catalog(root)

    def test_schema_and_category_errors_do_not_create_an_empty_green_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts/ci").mkdir(parents=True)
            path = root / "scripts/ci/test-classification.json"
            for catalog in ([], {"version": 2, "modules": {}},
                            {"version": 1, "modules": {"demo": []}},
                            {"version": 1, "modules": {"demo": {"complete": False}}},
                            {"version": 1, "modules": {"demo": {"complete": True, "files": {}}}}):
                with self.subTest(catalog=catalog):
                    path.write_text(json.dumps(catalog))
                    with self.assertRaises(ValueError):
                        load_catalog(root)


if __name__ == "__main__":
    unittest.main()
