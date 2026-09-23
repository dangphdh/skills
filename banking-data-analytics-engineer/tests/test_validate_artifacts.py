"""Tests for scripts/validate_artifacts.py (banking-data-analytics-engineer skill).

Uses the synthetic valid-retail-loan fixture, mutated per test in a temporary
directory. Exercises main() directly and the CLI via subprocess with --json.

Baseline note: the shipped fixture's query metrics mirror metric-catalog.csv
exactly, so the clean baseline reports no findings and --strict also passes.
Mirror drift introduced by a mutation is reported as a
CROSS_REF_METRIC_MISMATCH warning.
"""
import csv
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
VALIDATE_SCRIPT = SKILL_DIR / "scripts" / "validate_artifacts.py"
FIXTURE = SKILL_DIR / "tests" / "fixtures" / "valid-retail-loan"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "validate_artifacts_under_test", VALIDATE_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateArtifactsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.va = load_module()

    # -- helpers -----------------------------------------------------------

    def make_project(self):
        dest = self.tmp / "proj"
        shutil.copytree(FIXTURE, dest)
        return dest

    def run_cli(self, dest, *flags):
        proc = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT), str(dest), *flags],
            capture_output=True, text=True,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def report_of(self, dest, *flags):
        code, out, err = self.run_cli(dest, "--json", *flags)
        return code, json.loads(out)

    def issue_codes(self, report):
        return {finding["code"] for finding in report["issues"]}

    def warning_codes(self, report):
        return {finding["code"] for finding in report["warnings"]}

    def edit_json(self, dest, name, mutate):
        path = dest / name
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def edit_csv_rows(self, dest, name, mutate):
        """Read a CSV as dicts, mutate, and write back preserving headers."""
        path = dest / name
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        header, body = rows[0], rows[1:]
        dicts = [
            {header[i]: (row[i] if i < len(row) else "") for i in range(len(header))}
            for row in body
        ]
        mutate(dicts)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(
                [[d.get(col, "") for col in header] for d in dicts]
            )

    def _mkjunction(self, link, target):
        """Create an NTFS junction; returns False when unavailable."""
        try:
            proc = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True, text=True,
            )
        except OSError:
            return False
        return proc.returncode == 0

    def _force_remove_link(self, path):
        """Remove a junction/symlink itself (never its target); ignore errors."""
        try:
            os.rmdir(str(path))
        except OSError:
            pass

    # -- clean baseline ------------------------------------------------------

    def test_baseline_fixture_exit_codes_and_strict(self):
        dest = self.make_project()
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "clean")
        self.assertEqual(report["summary"], {"issue_count": 0, "warning_count": 0})
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["warnings"], [])
        code, _, _ = self.run_cli(dest, "--strict")
        self.assertEqual(code, 0)

    def test_json_report_contract(self):
        dest = self.make_project()
        self.edit_json(dest, "query-spec.json", lambda d: d.update(metrics=[]))
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)
        self.assertEqual(
            set(report), {"project_dir", "status", "issues", "warnings", "summary"}
        )
        self.assertEqual(
            set(report["summary"]), {"issue_count", "warning_count"}
        )
        for finding in report["issues"] + report["warnings"]:
            self.assertEqual(set(finding), {"code", "path", "message"})
        self.assertEqual([w["code"] for w in report["warnings"]], ["QUERY_NO_METRICS"])

    def test_function_api_main_and_validate_project(self):
        dest = self.make_project()
        self.assertEqual(self.va.main([str(dest)]), 0)
        report = self.va.validate_project(dest)
        self.assertEqual(report["status"], "clean")
        self.assertEqual(report["summary"]["issue_count"], 0)

    def test_human_output_is_readable(self):
        dest = self.make_project()
        code, out, _ = self.run_cli(dest)
        self.assertEqual(code, 0)
        self.assertIn("CLEAN", out)

    # -- exit code 2 input/config errors -------------------------------------

    def test_missing_project_dir_exit_two(self):
        code, _, err = self.run_cli(self.tmp / "nope")
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())

    def test_missing_analysis_spec_exit_two(self):
        dest = self.make_project()
        (dest / "analysis-spec.json").unlink()
        code, _, err = self.run_cli(dest)
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())

    def test_unparseable_analysis_spec_exit_two(self):
        dest = self.make_project()
        (dest / "analysis-spec.json").write_text("{ not json", encoding="utf-8")
        code, _, _ = self.run_cli(dest)
        self.assertEqual(code, 2)

    # -- required files --------------------------------------------------------

    def test_missing_required_artifact_file(self):
        dest = self.make_project()
        (dest / "quality-rules.csv").unlink()
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("ARTIFACT_FILE_MISSING", self.issue_codes(report))
        self.assertTrue(
            any(f["path"] == "quality-rules.csv" for f in report["issues"])
        )
        # quality_checks references can no longer resolve: reported as skipped.
        self.assertIn("CROSS_REF_SKIPPED", self.warning_codes(report))

    def test_artifact_not_declared_for_enabled_workstream(self):
        dest = self.make_project()
        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d["artifacts"].update(reconciliation_plan=""),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("ARTIFACT_NOT_DECLARED", self.issue_codes(report))

    def test_unknown_workstream_rejected(self):
        dest = self.make_project()
        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d["enabled_workstreams"].append("crypto-mining"),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("WORKSTREAM_UNKNOWN", self.issue_codes(report))

    def test_duplicate_workstreams_flagged(self):
        dest = self.make_project()
        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d.update(enabled_workstreams=["data-mining", "data-mining"]),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("WORKSTREAM_DUPLICATE", self.issue_codes(report))

    # -- evidence ledger and references ----------------------------------------

    def test_missing_evidence_row_breaks_references(self):
        dest = self.make_project()

        def drop_evd0003(rows):
            rows[:] = [r for r in rows if r["evidence_id"] != "EVD-0003"]

        self.edit_csv_rows(dest, "evidence-ledger.csv", drop_evd0003)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("EVIDENCE_REF_BROKEN", self.issue_codes(report))

    def test_duplicate_and_blank_ids(self):
        dest = self.make_project()

        def duplicate(rows):
            rows.append(dict(rows[0]))

        self.edit_csv_rows(dest, "evidence-ledger.csv", duplicate)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("ID_DUPLICATE", self.issue_codes(report))

    def test_invalid_evidence_state(self):
        dest = self.make_project()

        def bad_state(rows):
            rows[1]["state"] = "confirmed"

        self.edit_csv_rows(dest, "evidence-ledger.csv", bad_state)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("EVIDENCE_STATE_INVALID", self.issue_codes(report))

    def test_unavailable_evidence_ledger_warns_without_cascade(self):
        dest = self.make_project()
        # Invalid UTF-8 makes the file unreadable as text/CSV.
        (dest / "evidence-ledger.csv").write_bytes(b"evidence_id,state\n\xff\xfebroken\n")
        code, report = self.report_of(dest)
        codes = self.issue_codes(report)
        self.assertIn("CSV_READ_FAILED", codes)
        # No cascade of unknown-ref findings; one deterministic skip warning.
        self.assertNotIn("EVIDENCE_REF_BROKEN", codes)
        self.assertIn("CROSS_REF_SKIPPED", self.warning_codes(report))
        skipped = [
            w for w in report["warnings"] if w["code"] == "CROSS_REF_SKIPPED"
        ]
        self.assertTrue(any("evidence-ledger.csv" in w["message"] for w in skipped))

    def test_missing_source_inventory_warns_without_fake_refs(self):
        dest = self.make_project()
        (dest / "source-inventory.csv").unlink()
        code, report = self.report_of(dest)
        codes = self.issue_codes(report)
        self.assertIn("ARTIFACT_FILE_MISSING", codes)
        self.assertNotIn("CROSS_REF_SOURCE_UNKNOWN", codes)
        self.assertIn("CROSS_REF_SKIPPED", self.warning_codes(report))

    # -- model spec --------------------------------------------------------------

    def test_broken_relationship_endpoint(self):
        dest = self.make_project()

        def break_endpoint(data):
            data["relationships"][0]["to_entity"] = "ENT-999"

        self.edit_json(dest, "model-spec.json", break_endpoint)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("RELATIONSHIP_ENDPOINT_UNKNOWN", self.issue_codes(report))

    def test_entity_missing_grain_keys_and_evidence(self):
        dest = self.make_project()

        def strip_entity(data):
            entity = data["entities"][0]
            entity["grain"] = ""
            entity["business_keys"] = []
            entity["evidence_ids"] = []

        self.edit_json(dest, "model-spec.json", strip_entity)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        for expected in (
            "MODEL_ENTITY_GRAIN_MISSING",
            "MODEL_ENTITY_KEYS_MISSING",
            "EVIDENCE_REF_MISSING",
        ):
            self.assertIn(expected, codes)

    def test_model_entity_and_attribute_required_fields(self):
        dest = self.make_project()

        def strip_fields(data):
            entity = data["entities"][0]
            entity.pop("name")
            entity.pop("temporal_strategy")
            del entity["attributes"][1]["logical_type"]

        self.edit_json(dest, "model-spec.json", strip_fields)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        self.assertIn("MODEL_ENTITY_FIELD_MISSING", codes)
        self.assertIn("MODEL_ATTRIBUTE_FIELD_MISSING", codes)
        entity_fields = [
            f for f in report["issues"] if f["code"] == "MODEL_ENTITY_FIELD_MISSING"
        ]
        self.assertEqual(
            {f["message"] for f in entity_fields},
            {"entities[1]: 'name' must be a non-blank string",
             "entities[1]: 'temporal_strategy' must be a non-blank string"},
        )

    # -- query spec ----------------------------------------------------------------

    def test_query_missing_grain_sources_time_currency(self):
        dest = self.make_project()

        def strip_query(data):
            data["result_grain"] = ""
            data["verified_sources"] = []
            data["time_basis"]["cutoff"] = ""
            data["currency_basis"]["currencies"] = []

        self.edit_json(dest, "query-spec.json", strip_query)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        for expected in (
            "QUERY_GRAIN_MISSING",
            "QUERY_SOURCES_MISSING",
            "QUERY_TIME_MISSING",
            "QUERY_CURRENCY_MISSING",
        ):
            self.assertIn(expected, codes)

    def test_unknown_dialect_requires_unvalidated_flag(self):
        dest = self.make_project()

        def unknown_dialect(data):
            data["dialect"] = "hypersql"
            data["dialect_validation"] = ""

        self.edit_json(dest, "query-spec.json", unknown_dialect)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("STATE_INVALID", self.issue_codes(report))

        def mark_validated(data):
            data["dialect_validation"] = "DIALECT_VALIDATED"

        self.edit_json(dest, "query-spec.json", mark_validated)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("DIALECT_UNVALIDATED_REQUIRED", self.issue_codes(report))

        def mark_unvalidated(data):
            data["dialect_validation"] = "DIALECT_UNVALIDATED"

        self.edit_json(dest, "query-spec.json", mark_unvalidated)
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)
        self.assertNotIn("DIALECT_UNVALIDATED_REQUIRED", self.issue_codes(report))
        self.assertNotIn("STATE_INVALID", self.issue_codes(report))

    def test_known_dialect_requires_exact_validation_flag(self):
        dest = self.make_project()
        self.edit_json(
            dest, "query-spec.json",
            lambda d: d.update(dialect="postgresql", dialect_validation=""),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("STATE_INVALID", self.issue_codes(report))
        self.edit_json(
            dest, "query-spec.json",
            lambda d: d.update(dialect_validation="DIALECT_VALIDATED"),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)

    def test_platform_object_and_keys_required(self):
        dest = self.make_project()
        self.edit_json(dest, "analysis-spec.json", lambda d: d.pop("platform"))
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("JSON_FIELD_TYPE", self.issue_codes(report))
        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d.update(platform={"dialect": "postgresql"}),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        missing = [
            f for f in report["issues"] if f["code"] == "REQUIRED_FIELD_MISSING"
        ]
        self.assertTrue(
            any("'platform.dialect_validation' is required" in f["message"] for f in missing)
        )

    # -- reconciliation plan ---------------------------------------------------------

    def test_multi_currency_needs_two_currencies_and_grouping(self):
        dest = self.make_project()

        def one_currency(data):
            data["currency_controls"]["currencies"] = ["VND"]

        self.edit_json(dest, "reconciliation-plan.json", one_currency)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("RECON_CURRENCY_INSUFFICIENT", self.issue_codes(report))

        def drop_grouping(data):
            data["currency_controls"]["currencies"] = ["VND", "USD"]
            data["controls"][0]["group_by"] = ["branch_code"]
            data["controls"][1]["group_by"] = ["branch_code"]

        self.edit_json(dest, "reconciliation-plan.json", drop_grouping)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("RECON_CURRENCY_GROUPING", self.issue_codes(report))

    def test_tolerance_missing_and_bad_decimal_format(self):
        dest = self.make_project()

        def bad_tolerances(data):
            data["tolerances"]["amount_absolute"] = ""
            data["tolerances"]["amount_percentage"] = "1,5"

        self.edit_json(dest, "reconciliation-plan.json", bad_tolerances)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        self.assertIn("RECON_TOLERANCE_MISSING", codes)
        self.assertIn("RECON_TOLERANCE_FORMAT", codes)

    def test_reconciliation_missing_keys_time_and_owner(self):
        dest = self.make_project()

        def strip_recon(data):
            data["matching_keys"] = []
            data["time_context"]["cutoff"] = ""
            data["time_context"]["timezone"] = ""
            data["exception_management"]["owner"] = ""

        self.edit_json(dest, "reconciliation-plan.json", strip_recon)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        for expected in (
            "RECON_KEYS_MISSING",
            "RECON_TIME_MISSING",
            "RECON_EXCEPTION_MISSING",
        ):
            self.assertIn(expected, codes)

    # -- mappings and quality rules ----------------------------------------------------

    def test_incomplete_mapping_implicit_transformation_and_default(self):
        dest = self.make_project()

        def strip_mapping(rows):
            for row in rows:
                if row["mapping_id"] in {"MAP-002", "MAP-004"}:
                    row["transformation_rule"] = ""
                    row["default_rule"] = ""

        self.edit_csv_rows(dest, "source-to-target.csv", strip_mapping)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        self.assertIn("MAPPING_IMPLICIT_TRANSFORMATION", codes)
        self.assertIn("MAPPING_IMPLICIT_DEFAULT", codes)

    def test_nullable_zero_rejected_without_default_cascade(self):
        dest = self.make_project()

        def bad_nullable(rows):
            rows[0]["nullable"] = "0"
            rows[0]["default_rule"] = ""

        self.edit_csv_rows(dest, "source-to-target.csv", bad_nullable)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        s2t_codes = {
            f["code"] for f in report["issues"] if f["path"] == "source-to-target.csv"
        }
        self.assertIn("MAPPING_NULLABLE_INVALID", s2t_codes)
        # "0" is not a recognized nullable value, so it must not additionally
        # be treated as a not-nullable row requiring a default rule.
        self.assertNotIn("MAPPING_IMPLICIT_DEFAULT", s2t_codes)

    def test_quality_rule_owner_and_evidence_required(self):
        dest = self.make_project()

        def strip_rule(rows):
            rows[0]["owner"] = ""
            rows[0]["evidence_ids"] = ""

        self.edit_csv_rows(dest, "quality-rules.csv", strip_rule)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        self.assertIn("QUALITY_OWNER_MISSING", codes)
        self.assertIn("EVIDENCE_REF_MISSING", codes)

    # -- CSV headers -----------------------------------------------------------------

    def test_extra_csv_headers_are_allowed(self):
        dest = self.make_project()
        path = dest / "glossary.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        for row in rows:
            row.append("extra")
        with path.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerows(rows)
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)

    def test_missing_required_csv_header(self):
        dest = self.make_project()
        path = dest / "glossary.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        header = rows[0]
        header[header.index("definition")] = "description"
        with path.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerows(rows)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("CSV_HEADER_MISSING", self.issue_codes(report))

    # -- states and human approval ---------------------------------------------------

    def test_invalid_and_prohibited_statuses(self):
        dest = self.make_project()
        self.edit_json(
            dest, "analysis-spec.json", lambda d: d.update(status="published")
        )
        self.edit_json(
            dest, "model-spec.json", lambda d: d.update(status="production_ready")
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        self.assertIn("STATE_INVALID", codes)
        self.assertIn("STATUS_PROHIBITED", codes)

    def test_enum_case_is_enforced(self):
        dest = self.make_project()
        self.edit_json(
            dest, "analysis-spec.json", lambda d: d.update(status="DRAFT")
        )
        self.edit_csv_rows(
            dest, "evidence-ledger.csv", lambda rows: rows[0].update(confidence="HIGH")
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        self.assertIn("STATE_INVALID", codes)
        self.assertIn("EVIDENCE_CONFIDENCE_INVALID", codes)

    def test_human_validated_requires_name_and_date(self):
        dest = self.make_project()
        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d.update(status="human_validated"),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("HUMAN_APPROVAL_INCOMPLETE", self.issue_codes(report))

        def approve(data):
            data["human_approval"] = {"name": "Example Reviewer", "date": "2026-09-23"}

        self.edit_json(dest, "analysis-spec.json", approve)
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)
        self.assertNotIn("HUMAN_APPROVAL_INCOMPLETE", self.issue_codes(report))

    def test_human_approval_date_must_be_iso(self):
        dest = self.make_project()
        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d.update(
                status="human_validated",
                human_approval={"name": "Example Reviewer", "date": "09/23/2026"},
            ),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        self.assertIn("HUMAN_APPROVAL_DATE_INVALID", codes)
        self.assertNotIn("HUMAN_APPROVAL_INCOMPLETE", codes)

        def impossible_calendar(data):
            data["human_approval"]["date"] = "2026-02-30"

        self.edit_json(dest, "analysis-spec.json", impossible_calendar)
        code, report = self.report_of(dest)
        self.assertIn("HUMAN_APPROVAL_DATE_INVALID", self.issue_codes(report))

        def valid_date(data):
            data["human_approval"]["date"] = "2026-09-23"

        self.edit_json(dest, "analysis-spec.json", valid_date)
        code, report = self.report_of(dest)
        self.assertNotIn("HUMAN_APPROVAL_DATE_INVALID", self.issue_codes(report))

    # -- strict warnings ---------------------------------------------------------------

    def test_strict_escalates_warnings_to_failure(self):
        dest = self.make_project()
        self.edit_json(dest, "query-spec.json", lambda d: d.update(metrics=[]))
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "warnings")
        self.assertEqual(report["summary"]["issue_count"], 0)
        self.assertEqual(report["summary"]["warning_count"], 1)
        code, _, _ = self.run_cli(dest, "--strict")
        self.assertEqual(code, 1)

    # -- secret and account-number heuristic ----------------------------------------------

    def test_secrets_and_account_numbers_detected_but_redacted(self):
        dest = self.make_project()
        (dest / "notes.md").write_text(
            "db_password = SuperSecretValue9\n"
            "connect via postgres://admin:hunter2@db.internal.local:5432/fin\n"
            "test account 4111111111111111\n"
            "ordinary date 2026-06-30 and amount 1234567.89 are not findings\n",
            encoding="utf-8",
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        self.assertIn("SUSPECTED_SECRET", codes)
        self.assertIn("SUSPECTED_ACCOUNT_NUMBER", codes)
        raw = json.dumps(report)
        self.assertNotIn("SuperSecretValue9", raw)
        self.assertNotIn("hunter2", raw)
        self.assertNotIn("4111111111111111", raw)

    def test_oversize_files_are_streamed_and_truncation_reported(self):
        dest = self.make_project()
        cap = self.va.MAX_SCAN_BYTES
        # Secret inside the scanned prefix of an over-cap file.
        partial = dest / "partial-scan.log"
        partial.write_text("password = VisibleSecret1\n" + "x" * cap, encoding="utf-8")
        # Secret beyond the cap: never scanned, truncation reported instead.
        beyond = dest / "beyond-scan.log"
        beyond.write_text("x" * cap + "\npassword = HiddenSecret9\n", encoding="utf-8")
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        partial_codes = {
            f["code"] for f in report["issues"] if f["path"] == "partial-scan.log"
        }
        self.assertEqual(partial_codes, {"SUSPECTED_SECRET"})
        beyond_issues = [f for f in report["issues"] if f["path"] == "beyond-scan.log"]
        self.assertEqual(beyond_issues, [])
        truncated = {
            w["path"] for w in report["warnings"] if w["code"] == "SCAN_TRUNCATED"
        }
        self.assertEqual(truncated, {"partial-scan.log", "beyond-scan.log"})

    def test_match_straddling_chunk_boundary_is_found(self):
        dest = self.make_project()
        chunk = self.va.SCAN_CHUNK_BYTES
        # The newline gives \b before "password"; the match straddles the
        # 1 MiB chunk boundary so only the overlap window can see it whole.
        (dest / "straddle.log").write_text(
            "x" * (chunk - 11) + "\npassword = hunter2xyz\n", encoding="utf-8"
        )
        code, report = self.report_of(dest)
        straddle_codes = {
            f["code"] for f in report["issues"] if f["path"] == "straddle.log"
        }
        self.assertEqual(straddle_codes, {"SUSPECTED_SECRET"})

    # -- junction and symlink safety (Windows) -----------------------------------------

    @unittest.skipUnless(os.name == "nt", "junction tests require Windows")
    def test_junction_cycle_is_skipped_without_crashing(self):
        dest = self.make_project()
        self.addCleanup(shutil.rmtree, dest, ignore_errors=True)
        if not self._mkjunction(dest / "loop", dest):
            self.skipTest("junction creation unavailable")
        self.addCleanup(self._force_remove_link, dest / "loop")
        # Must complete without an unhandled exception and without hanging.
        code, report = self.report_of(dest)
        self.assertIn(code, (0, 1))
        self.assertEqual(report["issues"], [])
        self.assertIn("SCAN_SKIPPED_JUNCTION", self.warning_codes(report))
        loop_warnings = [
            w for w in report["warnings"] if w["path"] == "loop"
        ]
        self.assertTrue(loop_warnings)

    @unittest.skipUnless(os.name == "nt", "junction tests require Windows")
    def test_external_junction_contents_are_not_scanned(self):
        dest = self.make_project()
        self.addCleanup(shutil.rmtree, dest, ignore_errors=True)
        external = self.tmp / "outside-scan"
        external.mkdir()
        (external / "secret.txt").write_text(
            "password = REALSECRETVALUE7\n", encoding="utf-8"
        )
        if not self._mkjunction(dest / "extlink", external):
            self.skipTest("junction creation unavailable")
        self.addCleanup(self._force_remove_link, dest / "extlink")
        code, report = self.report_of(dest)
        # The external secret must not surface, and the junction is reported.
        self.assertEqual(report["issues"], [])
        self.assertIn("SCAN_SKIPPED_JUNCTION", self.warning_codes(report))
        raw = json.dumps(report)
        self.assertNotIn("REALSECRETVALUE7", raw)

    # -- contract vocabularies: evidence review vs glossary vs lifecycle -------

    def test_evidence_review_state_enum(self):
        dest = self.make_project()

        def bad(rows):
            rows[1]["validation_state"] = "approved"

        self.edit_csv_rows(dest, "evidence-ledger.csv", bad)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("EVIDENCE_REVIEW_STATE_INVALID", self.issue_codes(report))

    def test_glossary_review_state_enum_rejects_lifecycle_value(self):
        dest = self.make_project()

        def bad(rows):
            rows[0]["status"] = "draft"  # lifecycle value misused as glossary state

        self.edit_csv_rows(dest, "glossary.csv", bad)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("GLOSSARY_STATE_INVALID", self.issue_codes(report))

    # -- multi-currency controls group by a currency field ----------------------

    def test_multi_currency_controls_group_by_currency_field(self):
        dest = self.make_project()

        def bad_grouping(data):
            data["controls"][0]["type"] = "amount"  # monetary, needs currency field
            data["controls"][0]["group_by"] = ["VND", "branch_code"]  # value, not field

        self.edit_json(dest, "reconciliation-plan.json", bad_grouping)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("RECON_CURRENCY_GROUPING", self.issue_codes(report))

    def test_currency_grouping_only_required_for_monetary_controls(self):
        dest = self.make_project()

        def non_monetary_ungrouped(data):
            data["currency_controls"]["currencies"] = ["VND", "USD"]
            data["controls"][0]["group_by"] = ["branch_code"]     # type: count
            data["controls"][1]["group_by"] = ["currency_code"]   # type: amount

        self.edit_json(dest, "reconciliation-plan.json", non_monetary_ungrouped)
        code, report = self.report_of(dest)
        self.assertNotIn("RECON_CURRENCY_GROUPING", self.issue_codes(report))

        def monetary_ungrouped(data):
            data["controls"][1]["group_by"] = ["branch_code"]

        self.edit_json(dest, "reconciliation-plan.json", monetary_ungrouped)
        code, report = self.report_of(dest)
        self.assertIn("RECON_CURRENCY_GROUPING", self.issue_codes(report))

        def balance_type_ungrouped(data):
            data["controls"][1]["type"] = "balance"

        self.edit_json(dest, "reconciliation-plan.json", balance_type_ungrouped)
        code, report = self.report_of(dest)
        self.assertIn("RECON_CURRENCY_GROUPING", self.issue_codes(report))

    # -- cross-artifact references ----------------------------------------------

    def test_query_verified_source_cross_reference(self):
        dest = self.make_project()

        def bad(data):
            data["verified_sources"][0] = "extracts/unknown.csv"

        self.edit_json(dest, "query-spec.json", bad)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("CROSS_REF_SOURCE_UNKNOWN", self.issue_codes(report))

    def test_mapping_source_object_cross_reference(self):
        dest = self.make_project()

        def bad(rows):
            rows[0]["source_object"] = "extracts/unknown.csv"

        self.edit_csv_rows(dest, "source-to-target.csv", bad)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("CROSS_REF_SOURCE_UNKNOWN", self.issue_codes(report))

    def test_query_metric_id_cross_reference(self):
        dest = self.make_project()

        def bad(data):
            data["metrics"][0]["metric_id"] = "MTR-9999"

        self.edit_json(dest, "query-spec.json", bad)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("CROSS_REF_METRIC_UNKNOWN", self.issue_codes(report))

    def test_mapping_quality_check_cross_reference(self):
        dest = self.make_project()

        def bad(rows):
            for row in rows:
                if row["mapping_id"] == "MAP-001":
                    row["quality_checks"] = "QR-999"

        self.edit_csv_rows(dest, "source-to-target.csv", bad)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("CROSS_REF_QUALITY_RULE_UNKNOWN", self.issue_codes(report))

    # -- query metric mirror and currency vocabulary ------------------------------

    def test_query_metric_currency_vocabulary(self):
        dest = self.make_project()
        self.edit_json(
            dest, "query-spec.json",
            lambda d: d["metrics"][0].update(currency="USD"),  # ISO code: allowed
        )
        self.edit_json(
            dest, "query-spec.json",
            lambda d: d["metrics"][1].update(currency="banana"),  # not allowed
        )
        code, report = self.report_of(dest)
        invalid = [
            f for f in report["issues"] if f["code"] == "QUERY_METRIC_CURRENCY_INVALID"
        ]
        self.assertEqual(len(invalid), 1)
        self.assertIn("banana", invalid[0]["message"])

    def test_query_metric_mirror_mismatch_is_reported(self):
        dest = self.make_project()
        self.edit_json(
            dest, "query-spec.json",
            lambda d: d["metrics"][0].update(unit="kg", currency="USD"),
        )
        code, report = self.report_of(dest)
        mismatches = [
            w for w in report["warnings"] if w["code"] == "CROSS_REF_METRIC_MISMATCH"
        ]
        self.assertEqual(len(mismatches), 1)
        self.assertIn("metrics[1]", mismatches[0]["message"])
        self.assertIn("unit 'kg'", mismatches[0]["message"])
        self.assertIn("currency 'USD'", mismatches[0]["message"])

        def rename(data):
            data["metrics"][1].update(name="renamed_metric")

        self.edit_json(dest, "query-spec.json", rename)
        code, report = self.report_of(dest)
        mismatches = [
            w for w in report["warnings"] if w["code"] == "CROSS_REF_METRIC_MISMATCH"
        ]
        self.assertEqual(len(mismatches), 2)
        second = next(w for w in mismatches if "metrics[2]" in w["message"])
        self.assertIn("name 'renamed_metric'", second["message"])

        def realign(data):
            data["metrics"][0].update(unit="amount", currency="account_currency")
            data["metrics"][1].update(name="principal_event_count")

        self.edit_json(dest, "query-spec.json", realign)
        code, report = self.report_of(dest)
        self.assertEqual(
            [w for w in report["warnings"] if w["code"] == "CROSS_REF_METRIC_MISMATCH"],
            [],
        )

    # -- review summary headings --------------------------------------------------

    def test_review_summary_headings_required(self):
        dest = self.make_project()
        path = dest / "review-summary.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("## Known limitations", "## Caveats"), encoding="utf-8")
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("REVIEW_HEADING_MISSING", self.issue_codes(report))

    # -- schema version and required fields ----------------------------------------

    def test_schema_version_enforced(self):
        dest = self.make_project()
        self.edit_json(dest, "analysis-spec.json", lambda d: d.update(schema_version="2.0"))
        self.edit_json(dest, "model-spec.json", lambda d: d.update(schema_version="2.0"))
        self.edit_json(dest, "query-spec.json", lambda d: d.update(schema_version="2.0"))
        self.edit_json(
            dest, "reconciliation-plan.json", lambda d: d.update(schema_version="2.0")
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        issues = [f for f in report["issues"] if f["code"] == "SCHEMA_VERSION_INVALID"]
        self.assertEqual(len(issues), 4)

    def test_required_top_level_fields(self):
        dest = self.make_project()
        self.edit_json(
            dest, "analysis-spec.json", lambda d: d.update(business_question="")
        )
        self.edit_json(dest, "model-spec.json", lambda d: d.update(title=""))
        self.edit_json(dest, "query-spec.json", lambda d: d.update(population=""))
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        issues = [f for f in report["issues"] if f["code"] == "REQUIRED_FIELD_MISSING"]
        self.assertEqual(
            {f["path"] for f in issues},
            {"analysis-spec.json", "model-spec.json", "query-spec.json"},
        )

    def test_evidence_row_field_validation(self):
        dest = self.make_project()

        def bad(rows):
            rows[0]["source_locator"] = ""
            rows[0]["owner"] = ""
            rows[1]["confidence"] = "certain"

        self.edit_csv_rows(dest, "evidence-ledger.csv", bad)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        self.assertIn("EVIDENCE_LOCATOR_MISSING", codes)
        self.assertIn("EVIDENCE_OWNER_MISSING", codes)
        self.assertIn("EVIDENCE_CONFIDENCE_INVALID", codes)

    def test_query_metric_shape(self):
        dest = self.make_project()

        def bad(data):
            data["metrics"][0]["formula"] = ""
            data["metrics"][0]["currency"] = ""

        self.edit_json(dest, "query-spec.json", bad)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        issues = [
            f for f in report["issues"] if f["code"] == "QUERY_METRIC_FIELD_MISSING"
        ]
        self.assertEqual(len(issues), 2)

    def test_quality_rule_enums_and_threshold_gate(self):
        dest = self.make_project()

        def bad(rows):
            rows[0]["quality_dimension"] = "freshness"
            rows[0]["severity"] = "fatal"
            rows[1]["threshold"] = ""
            rows[1]["status"] = "ready_for_human_validation"

        self.edit_csv_rows(dest, "quality-rules.csv", bad)
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        codes = self.issue_codes(report)
        self.assertIn("QUALITY_DIMENSION_INVALID", codes)
        self.assertIn("QUALITY_SEVERITY_INVALID", codes)
        self.assertIn("QUALITY_THRESHOLD_MISSING", codes)

    # -- currency mode semantics ----------------------------------------------------

    def test_query_currency_mode_semantics(self):
        dest = self.make_project()
        self.edit_json(
            dest, "query-spec.json",
            lambda d: d["currency_basis"].update(mode="single_currency"),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("QUERY_CURRENCY_COUNT", self.issue_codes(report))

        self.edit_json(
            dest, "query-spec.json",
            lambda d: d["currency_basis"].update(mode="not_applicable"),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("QUERY_CURRENCY_NOT_APPLICABLE", self.issue_codes(report))

        self.edit_json(
            dest, "query-spec.json",
            lambda d: d["currency_basis"].update(mode="not_applicable", currencies=[]),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)

    def test_reconciliation_currency_mode_semantics(self):
        dest = self.make_project()
        self.edit_json(
            dest, "reconciliation-plan.json",
            lambda d: d["currency_controls"].update(mode="single_currency"),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("RECON_CURRENCY_COUNT", self.issue_codes(report))

        self.edit_json(
            dest, "reconciliation-plan.json",
            lambda d: d["currency_controls"].update(mode="not_applicable"),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("RECON_CURRENCY_NOT_APPLICABLE", self.issue_codes(report))

        self.edit_json(
            dest, "reconciliation-plan.json",
            lambda d: d["currency_controls"].update(
                mode="not_applicable", currencies=[]
            ),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)

    def test_currency_codes_must_be_iso_format(self):
        dest = self.make_project()
        self.edit_json(
            dest, "query-spec.json",
            lambda d: d["currency_basis"].update(currencies=["vnd"]),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("QUERY_CURRENCY_FORMAT_INVALID", self.issue_codes(report))

        self.edit_json(
            dest, "reconciliation-plan.json",
            lambda d: d["currency_controls"].update(currencies=["VND", "US1"]),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        self.assertIn("RECON_CURRENCY_FORMAT_INVALID", self.issue_codes(report))

    # -- project-level human approval gate -------------------------------------------

    def test_project_level_human_approval_gate(self):
        dest = self.make_project()
        self.edit_json(
            dest, "model-spec.json", lambda d: d.update(status="human_validated")
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        gate = [
            f for f in report["issues"] if f["code"] == "HUMAN_APPROVAL_INCOMPLETE"
        ]
        self.assertEqual(len(gate), 1)
        self.assertEqual(gate[0]["path"], "analysis-spec.json")
        self.assertIn("cannot verify", gate[0]["message"])

        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d.update(
                human_approval={"name": "Example Reviewer", "date": "2026-09-23"}
            ),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)

    def test_reconciliation_local_human_approval(self):
        dest = self.make_project()
        self.edit_json(
            dest, "reconciliation-plan.json",
            lambda d: d.update(status="human_validated"),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        approval_issues = [
            f for f in report["issues"] if f["code"] == "HUMAN_APPROVAL_INCOMPLETE"
        ]
        self.assertEqual(
            {f["path"] for f in approval_issues},
            {"analysis-spec.json", "reconciliation-plan.json"},
        )

        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d.update(
                human_approval={"name": "Example Reviewer", "date": "2026-09-23"}
            ),
        )
        self.edit_json(
            dest, "reconciliation-plan.json",
            lambda d: d.update(
                human_approval={"name": "Example Reviewer", "date": "2026-09-23"}
            ),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)

    # -- declared path escape -----------------------------------------------------------

    def test_artifact_path_escape_rejected(self):
        dest = self.make_project()
        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d["artifacts"].update(model_spec="../escape.json"),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        escapes = [
            f for f in report["issues"] if f["code"] == "ARTIFACT_PATH_ESCAPES"
        ]
        self.assertEqual(len(escapes), 1)
        self.assertNotIn("ARTIFACT_FILE_MISSING", self.issue_codes(report))

    # -- template placeholder gate ---------------------------------------------------------

    def test_placeholder_gate_blocks_ready_and_spares_draft(self):
        dest = self.make_project()
        self.edit_json(
            dest, "model-spec.json",
            lambda d: d.update(title="REPLACE_WITH_MODEL_TITLE"),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 0)  # draft scaffold: placeholder gate not applied
        self.assertNotIn("TEMPLATE_PLACEHOLDER_PRESENT", self.issue_codes(report))

        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d.update(
                status="ready_for_human_validation",
                business_question="REPLACE_WITH_BUSINESS_QUESTION",
            ),
        )
        code, report = self.report_of(dest)
        self.assertEqual(code, 1)
        placeholder_paths = {
            f["path"]
            for f in report["issues"]
            if f["code"] == "TEMPLATE_PLACEHOLDER_PRESENT"
        }
        self.assertEqual(
            placeholder_paths, {"analysis-spec.json", "model-spec.json"}
        )

    def test_placeholder_tokens_are_exact_and_include_new_tokens(self):
        dest = self.make_project()
        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d["project"].update(title="Legacy MY_QUERY_ID migration"),
        )
        self.edit_json(
            dest, "analysis-spec.json",
            lambda d: d.update(status="ready_for_human_validation"),
        )
        path = dest / "review-summary.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\nTemplate: PROJECT_TITLE due YYYY-MM-DD\n",
            encoding="utf-8",
        )
        code, report = self.report_of(dest)
        placeholder_paths = {
            f["path"]
            for f in report["issues"]
            if f["code"] == "TEMPLATE_PLACEHOLDER_PRESENT"
        }
        # "MY_QUERY_ID" is not flagged (substring), the exact tokens are.
        self.assertEqual(placeholder_paths, {"review-summary.md"})
        message = [
            f["message"] for f in report["issues"]
            if f["path"] == "review-summary.md"
        ][0]
        self.assertIn("PROJECT_TITLE", message)
        self.assertIn("YYYY-MM-DD", message)
        self.assertNotIn("QUERY_ID", message)


if __name__ == "__main__":
    unittest.main()
