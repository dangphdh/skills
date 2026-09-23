"""Tests for scripts/init_project.py (banking-data-analytics-engineer skill).

Standard library unittest only; exercises main() directly and the CLI via
subprocess, using temporary directories.
"""
import csv
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
INIT_SCRIPT = SKILL_DIR / "scripts" / "init_project.py"
TEMPLATES_DIR = SKILL_DIR / "assets" / "templates"
STAGING_PREFIX = ".init_project-staging-"

ALL_WORKSTREAMS = [
    "domain-modeling",
    "product-discovery",
    "data-mining",
    "quality-reconciliation",
]
ALL_FILES = {
    "analysis-spec.json",
    "evidence-ledger.csv",
    "source-inventory.csv",
    "glossary.csv",
    "model-spec.json",
    "query-spec.json",
    "metric-catalog.csv",
    "source-to-target.csv",
    "quality-rules.csv",
    "reconciliation-plan.json",
    "review-summary.md",
}
CSV_HEADERS = {
    "evidence-ledger.csv": "evidence_id,state,claim,source_locator,confidence,owner,validation_state",
    "source-inventory.csv": "source_id,object_name,object_type,definition,grain,candidate_keys,data_classification,evidence_ids,status",
    "glossary.csv": "term_id,term,aliases,definition,avoid_terms,evidence_ids,owner,status",
    "metric-catalog.csv": "metric_id,name,definition,numerator,denominator,grain,aggregation_behavior,time_basis,unit,currency,exclusions,owner,evidence_ids,status",
    "source-to-target.csv": "mapping_id,source_object,source_field,target_object,target_field,target_definition,target_logical_type,nullable,transformation_rule,join_rule,filter_rule,default_rule,grain_impact,data_classification,evidence_ids,quality_checks,unresolved_issue,owner,review_state",
    "quality-rules.csv": "rule_id,object_name,field_name,quality_dimension,rule_expression,severity,threshold,owner,evidence_ids,status",
}


def load_module():
    spec = importlib.util.spec_from_file_location("init_project_under_test", INIT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cli(*args):
    proc = subprocess.run(
        [sys.executable, str(INIT_SCRIPT)] + [str(a) for a in args],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def staging_leftovers(parent):
    return sorted(p.name for p in Path(parent).iterdir() if p.name.startswith(STAGING_PREFIX))


class InitProjectTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.init = load_module()

    def test_cli_all_workstreams_creates_every_artifact_and_sql_dir(self):
        dest = self.tmp / "proj"
        code, out, err = run_cli(
            dest, "--project-id", "PRJ-9001", "--title", "All workstreams",
            "--workstreams", *ALL_WORKSTREAMS,
        )
        self.assertEqual(code, 0, err)
        for name in ALL_FILES:
            self.assertTrue((dest / name).is_file(), f"missing {name}")
        self.assertTrue((dest / "sql").is_dir())
        manifest = json.loads((dest / "analysis-spec.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["project"]["id"], "PRJ-9001")
        self.assertEqual(manifest["project"]["title"], "All workstreams")
        self.assertEqual(sorted(manifest["enabled_workstreams"]), sorted(ALL_WORKSTREAMS))
        for key, path in manifest["artifacts"].items():
            self.assertTrue(path, f"artifacts.{key} should be declared")
            self.assertTrue((dest / path).is_file(), f"{key} -> {path} missing on disk")
        self.assertEqual(staging_leftovers(self.tmp), [])

    def test_manifest_has_canonical_shape(self):
        dest = self.tmp / "proj"
        self.assertEqual(
            self.init.main([
                str(dest), "--project-id", "PRJ-9002", "--title", "Shape",
                "--workstreams", "domain-modeling",
            ]),
            0,
        )
        manifest = json.loads((dest / "analysis-spec.json").read_text(encoding="utf-8"))
        for key in (
            "schema_version", "project", "status", "enabled_workstreams",
            "business_question", "intended_decision", "environment",
            "data_classification", "time_context", "platform", "owners",
            "human_approval", "artifacts",
        ):
            self.assertIn(key, manifest)
        self.assertEqual(
            sorted(manifest["artifacts"]),
            sorted([
                "evidence_ledger", "source_inventory", "glossary", "model_spec",
                "query_spec", "metric_catalog", "source_to_target", "quality_rules",
                "reconciliation_plan", "review_summary",
            ]),
        )

    def test_single_workstream_copies_only_relevant_artifacts(self):
        dest = self.tmp / "mining"
        self.assertEqual(
            self.init.main([
                str(dest), "--project-id", "PRJ-9003", "--title", "Mining only",
                "--workstreams", "data-mining",
            ]),
            0,
        )
        for name in ("analysis-spec.json", "review-summary.md", "evidence-ledger.csv",
                     "source-inventory.csv", "query-spec.json", "metric-catalog.csv"):
            self.assertTrue((dest / name).is_file(), f"missing {name}")
        for name in ("model-spec.json", "reconciliation-plan.json",
                     "source-to-target.csv", "quality-rules.csv"):
            self.assertFalse((dest / name).exists(), f"{name} should not be copied")
        self.assertTrue((dest / "sql").is_dir(), "data-mining must create sql/")
        manifest = json.loads((dest / "analysis-spec.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["artifacts"]["query_spec"], "query-spec.json")
        self.assertEqual(manifest["artifacts"]["model_spec"], "")

    def test_quality_reconciliation_artifacts_without_sql(self):
        dest = self.tmp / "recon"
        self.assertEqual(
            self.init.main([
                str(dest), "--project-id", "PRJ-9004", "--title", "Recon only",
                "--workstreams", "quality-reconciliation",
            ]),
            0,
        )
        for name in ("source-to-target.csv", "quality-rules.csv", "reconciliation-plan.json"):
            self.assertTrue((dest / name).is_file())
        self.assertFalse((dest / "sql").exists())
        self.assertFalse((dest / "query-spec.json").exists())

    def test_refuses_to_overwrite_non_empty_destination(self):
        dest = self.tmp / "occupied"
        dest.mkdir()
        sentinel = dest / "keep.txt"
        sentinel.write_text("do not touch", encoding="utf-8")
        code, _, err = run_cli(
            dest, "--project-id", "PRJ-9005", "--title", "Clash",
            "--workstreams", "data-mining",
        )
        self.assertEqual(code, 2)
        self.assertIn("error", err.lower())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "do not touch")
        self.assertEqual(staging_leftovers(self.tmp), [])

    def test_allows_existing_empty_destination(self):
        dest = self.tmp / "empty"
        dest.mkdir()
        code, _, err = run_cli(
            dest, "--project-id", "PRJ-9006", "--title", "Empty ok",
            "--workstreams", "data-mining",
        )
        self.assertEqual(code, 0, err)

    def test_unknown_workstream_is_an_input_error(self):
        with self.assertRaises(SystemExit) as ctx:
            self.init.main([
                str(self.tmp / "bad"), "--project-id", "PRJ-9007", "--title", "Bad",
                "--workstreams", "not-a-workstream",
            ])
        self.assertEqual(ctx.exception.code, 2)

    def test_missing_required_arguments_is_an_input_error(self):
        with self.assertRaises(SystemExit) as ctx:
            self.init.main([str(self.tmp / "bad")])
        self.assertEqual(ctx.exception.code, 2)

    def test_copied_csv_templates_have_exact_headers_and_no_rows(self):
        dest = self.tmp / "csvcheck"
        self.assertEqual(
            self.init.main([
                str(dest), "--project-id", "PRJ-9008", "--title", "CSV",
                "--workstreams", *ALL_WORKSTREAMS,
            ]),
            0,
        )
        for name, header in CSV_HEADERS.items():
            with (dest / name).open(newline="", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(",".join(rows[0]), header, name)
            self.assertEqual(len(rows), 1, f"{name} must be header-only")

    def test_no_credentials_or_env_files_are_created(self):
        dest = self.tmp / "clean"
        self.assertEqual(
            self.init.main([
                str(dest), "--project-id", "PRJ-9009", "--title", "No secrets",
                "--workstreams", *ALL_WORKSTREAMS,
            ]),
            0,
        )
        created = {p.name for p in dest.rglob("*") if p.is_file()}
        self.assertFalse(any(name.startswith(".env") for name in created))
        banned = ("connectors", "credentials")
        self.assertFalse(any(name in banned for name in created))

    # -- workstream deduplication ---------------------------------------------

    def test_duplicate_workstreams_are_deduped_keeping_first_seen_order(self):
        dest = self.tmp / "dedup"
        self.assertEqual(
            self.init.main([
                str(dest), "--project-id", "PRJ-9010", "--title", "Dedup",
                "--workstreams", "data-mining", "domain-modeling", "data-mining",
            ]),
            0,
        )
        manifest = json.loads((dest / "analysis-spec.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["enabled_workstreams"], ["data-mining", "domain-modeling"])

    def test_dedupe_helper_preserves_first_seen_order(self):
        self.assertEqual(
            self.init.dedupe_workstreams(
                ["quality-reconciliation", "data-mining", "quality-reconciliation"]
            ),
            ["quality-reconciliation", "data-mining"],
        )

    # -- review summary identity fill ------------------------------------------

    def test_review_summary_identity_placeholders_are_filled(self):
        dest = self.tmp / "review"
        self.assertEqual(
            self.init.main([
                str(dest), "--project-id", "PRJ-9011", "--title", "Fill Me In",
                "--workstreams", "domain-modeling",
            ]),
            0,
        )
        text = (dest / "review-summary.md").read_text(encoding="utf-8")
        self.assertIn("PRJ-9011", text)
        self.assertIn("Fill Me In", text)
        self.assertNotIn("PROJECT_ID", text)
        self.assertNotIn("PROJECT_TITLE", text)

    # -- atomic scaffold ---------------------------------------------------------

    def test_missing_template_is_atomic_and_retryable(self):
        partial_templates = self.tmp / "templates-partial"
        shutil.copytree(TEMPLATES_DIR, partial_templates)
        (partial_templates / "metric-catalog.csv").unlink()
        dest = self.tmp / "atomic"
        with self.assertRaises(FileNotFoundError):
            self.init.build_project(
                dest, "PRJ-9012", "Atomic", ["data-mining"],
                templates_dir=partial_templates,
            )
        # Nothing was created at the destination and no staging dirs remain.
        self.assertFalse(dest.exists())
        self.assertEqual(staging_leftovers(self.tmp), [])

        # Retry with the complete template set succeeds into the same path.
        full_templates = self.tmp / "templates-full"
        shutil.copytree(TEMPLATES_DIR, full_templates)
        created = self.init.build_project(
            dest, "PRJ-9012", "Atomic", ["data-mining"],
            templates_dir=full_templates,
        )
        self.assertTrue((dest / "metric-catalog.csv").is_file())
        self.assertTrue((dest / "analysis-spec.json").is_file())
        self.assertTrue(created)
        for path in created:
            self.assertTrue(path.is_file(), f"{path} should exist after retry")
        self.assertEqual(staging_leftovers(self.tmp), [])

    def test_failed_build_into_existing_empty_destination_preserves_it(self):
        partial_templates = self.tmp / "templates-partial2"
        shutil.copytree(TEMPLATES_DIR, partial_templates)
        (partial_templates / "glossary.csv").unlink()
        dest = self.tmp / "empty-then-fail"
        dest.mkdir()
        with self.assertRaises(FileNotFoundError):
            self.init.build_project(
                dest, "PRJ-9013", "EmptyDest", ["domain-modeling"],
                templates_dir=partial_templates,
            )
        self.assertTrue(dest.is_dir())
        self.assertEqual(list(dest.iterdir()), [])
        self.assertEqual(staging_leftovers(self.tmp), [])


if __name__ == "__main__":
    unittest.main()
