from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        self.assertEqual(set(catalog["modules"]), {
            "channel", "resource", "work", "agent", "harnesswork", "method",
            "foundation", "ontology",
        })
        for module, entry in catalog["modules"].items():
            discovered = {
                p.relative_to(ROOT).as_posix()
                for p in (ROOT / "tests" / module).rglob("test_*.py")
            }
            discovered.update(catalog_module.MODULE_EXTRA_TESTS.get(module, []))
            self.assertEqual(set(entry["files"]), discovered)

    def test_pure_test_changes_do_not_schedule_product_integration_or_e2e(self):
        for path in ("tests/resource/test_frontmatter.py", "tests/channel/test_host.py",
                     "tests/channel/test_session_work_adapter.py", "tests/work/test_runtime.py",
                     "tests/work/test_event_log.py", "tests/agent/test_proxy.py",
                     "tests/agent/test_agent_loop.py", "tests/examples/test_agent_examples.py",
                     "tests/harnesswork/integrations/test_session.py",
                     "tests/ontology/test_typed_query.py",
                     "tests/harnesswork/fixtures/legacy_coding_plan.jsonl",
                     "tests/harnesswork/fixtures/legacy_coding_plan_projection.json",
                     "tests/method/test_method_loader.py", "tests/method/test_runtime.py",
                     "tests/foundation/test_json_contract.py",
                     "tests/foundation/observability/test_sinks.py"):
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
        fixture = "tests/harnesswork/fixtures/legacy_coding_plan.jsonl"
        self.assertTrue(select([fixture, "src/loushang/harnesswork/runtime.py"], root=ROOT, pr_fast=True)["e2e"])
        self.assertTrue(select([fixture, "tests/conftest.py"], root=ROOT, pr_fast=True)["e2e"])
        self.assertTrue(select(["tests/harnesswork/fixtures/new_shared.json"], root=ROOT, pr_fast=True)["e2e"])

    def test_classified_module_runner_has_static_checks_and_full_reviewed_set(self):
        for module in ("channel", "resource", "work", "agent", "harnesswork", "method", "foundation"):
            planned = commands(f"unit_{module}", root=ROOT)
            self.assertEqual(len(planned), 2)
            self.assertIn("ruff", planned[0])
            for path in module_unit_paths(module, root=ROOT):
                self.assertIn(path, planned[1])
                self.assertEqual(planned[1].count(path), 1)
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

    def test_owned_extra_tests_are_required_and_directory_extras_expand_to_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts/ci").mkdir(parents=True)
            (root / "tests/demo").mkdir(parents=True)
            (root / "tests/contracts").mkdir(parents=True)
            files = ["tests/demo/test_one.py", "tests/contracts/test_extra.py"]
            for file in files:
                (root / file).write_text("def test_example(): pass\n")
            entry = {"complete": True, "files": {
                file: {"category": "contract", "assertion": "reviewed behavior"} for file in files}}
            path = root / "scripts/ci/test-classification.json"
            path.write_text(json.dumps({"version": 1, "modules": {"demo": entry}}))
            with patch.dict(catalog_module.MODULE_EXTRA_TESTS, {"demo": ["tests/contracts"]}):
                self.assertEqual(module_unit_paths("demo", root=root), sorted(files))
                entry["files"].pop(files[1])
                path.write_text(json.dumps({"version": 1, "modules": {"demo": entry}}))
                with self.assertRaisesRegex(ValueError, "missing=.*test_extra"):
                    load_catalog(root)
            with patch.dict(catalog_module.MODULE_EXTRA_TESTS, {"demo": ["tests/absent.py"]}):
                with self.assertRaisesRegex(ValueError, "missing module regression"):
                    load_catalog(root)

    def test_classified_directory_extras_are_not_collected_again(self):
        paths = ["tests/ai/test_auth.py", "tests/protocols/test_protocol_contracts.py",
                 "tests/examples/test_ai_examples.py", "tests/examples/test_auth_examples.py"]
        with patch("run_checks.module_unit_paths", return_value=paths):
            command = commands("unit_ai", root=ROOT)[-1]
        self.assertNotIn("tests/protocols", command)
        for path in paths:
            self.assertEqual(command.count(path), 1)

    def test_dedicated_fixture_requires_existing_path_and_reviewed_consumers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts/ci").mkdir(parents=True)
            (root / "tests/demo").mkdir(parents=True)
            test = "tests/demo/test_one.py"
            fixture = "tests/demo/golden.json"
            (root / test).write_text("def test_one(): pass\n")
            (root / fixture).write_text("{}")
            role = {"category": "contract", "assertion": "golden contract", "consumers": [test]}
            entry = {"complete": True, "files": {test: {
                "category": "unit", "assertion": "one behavior"}}, "fixtures": {fixture: role}}
            path = root / "scripts/ci/test-classification.json"
            def write():
                path.write_text(json.dumps({"version": 1, "modules": {"demo": entry}}))
            write()
            self.assertEqual(catalog_module.reviewed_unit_owner(fixture, catalog=load_catalog(root)), "demo")
            self.assertEqual(module_unit_paths("demo", root=root), [test])
            for consumers in ([], ["tests/other/test_two.py"], [test, test], test):
                role["consumers"] = consumers
                write()
                with self.subTest(consumers=consumers), self.assertRaises(ValueError):
                    load_catalog(root)
            role["consumers"] = [test]
            write()
            (root / fixture).unlink()
            with self.assertRaisesRegex(ValueError, "missing dedicated fixture"):
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
