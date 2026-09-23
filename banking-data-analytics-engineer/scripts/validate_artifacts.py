#!/usr/bin/env python3
"""validate_artifacts.py - structural validator for banking data analytics projects.

Validates a project scaffolded by init_project.py against
references/artifact-contracts.md. All checks are STRUCTURAL: file presence,
JSON/CSV shape, vocabularies, evidence/cross-artifact references, and internal
consistency. This tool never certifies business correctness, regulatory
compliance, or production readiness, and it never connects to a database,
network, or BI system. Artifact content is treated as data only; nothing is
executed or evaluated. Human-approval checks record field presence only; the
tool cannot verify who entered a value.

Usage:
  python validate_artifacts.py PROJECT_DIR [--json] [--strict]

Exit codes:
  0  clean or warnings only (without --strict)
  1  issues found (or any warnings when --strict is given)
  2  input/config error (project dir or analysis-spec.json unusable)

The JSON report shape is:
  {"project_dir": str, "status": "clean"|"warnings"|"issues",
   "issues": [{"code", "path", "message"}, ...],
   "warnings": [...], "summary": {"issue_count", "warning_count"}}
Findings are sorted by (path, code, message) for deterministic output.

Checking notes:
- Contract enums are matched case-exactly (e.g. "Draft" is invalid).
- `dialect_validation` must be exactly DIALECT_UNVALIDATED or DIALECT_VALIDATED;
  a blank or unrecognized dialect must stay DIALECT_UNVALIDATED, and the
  analysis-spec `platform` object with both keys is required.
- `human_approval.date` must be a valid ISO calendar date (YYYY-MM-DD) wherever
  an approval is required.
- Currency codes in `currency_basis`/`currency_controls` must be uppercase
  3-letter ISO-format tokens; mode `not_applicable` requires an empty list.
- Query metric `currency` must be an ISO 4217 code, `account_currency`, or
  `not_applicable`. When a query metric's metric_id exists in the metric
  catalog, name/unit/currency drift from the catalog is reported as a
  CROSS_REF_METRIC_MISMATCH warning.
- When a registry artifact (evidence ledger, source inventory, quality rules,
  metric catalog) cannot be validated, dependent cross-reference checks are
  skipped and one CROSS_REF_SKIPPED warning is emitted instead of cascading
  unknown-reference issues.

Heuristic safety scan (not a complete PII or secret scanner): regular project
files are scanned for obvious credential assignments, connection URIs with
embedded credentials, and 13-19 digit account/card-like number sequences. Files
are streamed in bounded chunks (with overlap) up to MAX_SCAN_BYTES bytes per
file; larger files produce a SCAN_TRUNCATED warning and their remainder is not
scanned. The traversal never follows symbolic links or Windows reparse-point
junctions, never reads outside the project directory, and is bounded by
MAX_SCAN_FILES and MAX_SCAN_DEPTH; entries it deliberately skips or cannot read
produce deterministic SCAN_* warnings. Matches are reported as file path plus a
generic message only; matched values are never echoed, and ordinary ISO dates
or decimal amounts are not matched.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import re
import stat
import sys
from pathlib import Path

ANALYSIS_SPEC_FILENAME = "analysis-spec.json"
SCHEMA_VERSION = "1.0"

WORKSTREAMS = (
    "domain-modeling",
    "product-discovery",
    "data-mining",
    "quality-reconciliation",
)

WORKSTREAM_ARTIFACTS = {
    "domain-modeling": ("evidence_ledger", "source_inventory", "glossary", "model_spec"),
    "product-discovery": ("evidence_ledger", "source_inventory", "glossary", "model_spec"),
    "data-mining": ("evidence_ledger", "source_inventory", "query_spec", "metric_catalog"),
    "quality-reconciliation": (
        "evidence_ledger",
        "source_inventory",
        "source_to_target",
        "quality_rules",
        "reconciliation_plan",
    ),
}

ALWAYS_ARTIFACTS = ("analysis_spec", "review_summary")

# Registries whose contents other artifacts reference by id. When one of these
# cannot be validated, dependent cross-reference checks are skipped with a
# deterministic warning instead of cascading unknown-reference issues.
REGISTRY_KEYS = ("evidence_ledger", "source_inventory", "quality_rules", "metric_catalog")

REGISTRY_CROSS_REFS = (
    ("ledger_ids", "evidence_ledger", "evidence-ledger.csv",
     ("source_inventory", "glossary", "metric_catalog", "quality_rules",
      "source_to_target", "model_spec", "query_spec", "reconciliation_plan")),
    ("source_keys", "source_inventory", "source-inventory.csv",
     ("source_to_target", "query_spec")),
    ("quality_rule_ids", "quality_rules", "quality-rules.csv",
     ("source_to_target",)),
    ("metric_catalog_rows", "metric_catalog", "metric-catalog.csv",
     ("query_spec",)),
)

# Distinct vocabularies per artifact-contracts.md; never collapse them.
# All enum matching is case-exact.
LIFECYCLE_STATES = {"draft", "blocked", "ready_for_human_validation", "human_validated"}
GATEKEEP_STATES = {"ready_for_human_validation", "human_validated"}
PROHIBITED_STATES = {"production_ready"}
EVIDENCE_CLAIM_STATES = {"observed", "inferred", "assumed", "question"}
EVIDENCE_REVIEW_STATES = {"pending", "confirmed_by_human", "superseded"}
GLOSSARY_REVIEW_STATES = {"proposed", "validated_by_owner", "divergent_from_seed"}
CONFIDENCE_VALUES = {"high", "medium", "low"}
OBJECT_TYPES = {"table", "view", "file", "report", "document", "other"}
AGGREGATION_BEHAVIORS = {"additive", "semi_additive", "non_additive"}
METRIC_CURRENCY_SPECIAL = {"mixed", "account_currency", "not_applicable"}
QUERY_METRIC_CURRENCY_SPECIAL = {"account_currency", "not_applicable"}
QUALITY_DIMENSIONS = {
    "completeness", "uniqueness", "validity", "consistency", "timeliness", "accuracy",
}
QUALITY_SEVERITIES = {"blocker", "error", "warning"}
CURRENCY_MODES = {"single_currency", "multi_currency", "not_applicable"}
NULLABLE_VALUES = {"yes", "no", "true", "false", "y", "n"}
NULLABLE_FALSE_VALUES = {"no", "false", "n"}
# Control `type` is free text per the contract, not a contract enum; this
# case-insensitive set classifies which controls are monetary for the
# multi-currency grouping check only.
MONETARY_CONTROL_TYPES = {"amount", "sum", "balance"}
DIALECT_VALIDATION_VALUES = {"DIALECT_UNVALIDATED", "DIALECT_VALIDATED"}
DIALECT_UNVALIDATED = "DIALECT_UNVALIDATED"
KNOWN_DIALECTS = {
    "postgresql", "postgres", "mysql", "mariadb", "sqlite", "duckdb", "sqlserver",
    "oracle", "db2", "snowflake", "bigquery", "redshift", "databricks", "teradata",
    "spark", "trino", "presto", "hive",
}
REVIEW_SUMMARY_HEADINGS = (
    "## Purpose",
    "## Workstream notes",
    "## Evidence summary",
    "## Validation status",
    "## Human validation",
    "## Known limitations",
)

DECIMAL_STRING_RE = re.compile(r"^\d+(\.\d+)?$")
ISO_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
ISO_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
CURRENCY_FIELD_RE = re.compile(r"currency|ccy", re.IGNORECASE)
# Exact token matching so e.g. MY_QUERY_ID or PROJECT_IDEA do not match.
TEMPLATE_PLACEHOLDER_RE = re.compile(
    r"\b(REPLACE_WITH_\w+|PROJECT_ID|PROJECT_TITLE|MODEL_ID|QUERY_ID|"
    r"RECONCILIATION_ID|YYYY-MM-DD)\b"
)

CSV_REQUIRED_HEADERS = {
    "evidence-ledger.csv": [
        "evidence_id", "state", "claim", "source_locator", "confidence", "owner",
        "validation_state",
    ],
    "source-inventory.csv": [
        "source_id", "object_name", "object_type", "definition", "grain",
        "candidate_keys", "data_classification", "evidence_ids", "status",
    ],
    "glossary.csv": [
        "term_id", "term", "aliases", "definition", "avoid_terms", "evidence_ids",
        "owner", "status",
    ],
    "metric-catalog.csv": [
        "metric_id", "name", "definition", "numerator", "denominator", "grain",
        "aggregation_behavior", "time_basis", "unit", "currency", "exclusions",
        "owner", "evidence_ids", "status",
    ],
    "source-to-target.csv": [
        "mapping_id", "source_object", "source_field", "target_object", "target_field",
        "target_definition", "target_logical_type", "nullable", "transformation_rule",
        "join_rule", "filter_rule", "default_rule", "grain_impact",
        "data_classification", "evidence_ids", "quality_checks", "unresolved_issue",
        "owner", "review_state",
    ],
    "quality-rules.csv": [
        "rule_id", "object_name", "field_name", "quality_dimension", "rule_expression",
        "severity", "threshold", "owner", "evidence_ids", "status",
    ],
}

MAX_SCAN_BYTES = 2_000_000
SCAN_CHUNK_BYTES = 1_000_000
SCAN_OVERLAP_BYTES = 256
MAX_SCAN_FILES = 50_000
MAX_SCAN_DEPTH = 32

# Present on Windows only; 0x0400 is FILE_ATTRIBUTE_REPARSE_POINT (junctions,
# symlinks, and other links), which the safety scan never descends into.
_FILE_ATTRIBUTE_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

SECRET_ASSIGN_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|apikey|access[_-]?key|"
    r"access[_-]?token|auth[_-]?token|client[_-]?secret|private[_-]?key)\b"
    r"\s*[:=]\s*[\"']?([^\s\"']{4,})"
)
CONN_URI_CREDS_RE = re.compile(
    r"(?i)\b[a-z][a-z0-9+.\-]*://[^\s/:@\"']+:[^\s/@\"']+@"
)
ACCOUNT_LIKE_RE = re.compile(r"(?<![\w.,\-])\d{13,19}(?![\w.,\-])")
PLACEHOLDER_VALUE_RE = re.compile(
    r"(?i)^(null|none|true|false|tbd|todo|redacted|placeholder|changeme|change_me)"
    r"$|replace|^<|\.\.\.|example\.|your_"
)


class _ConfigError(Exception):
    """Raised when the project directory or manifest is unusable (exit 2)."""


def _split_ids(value):
    """Split a CSV evidence_ids/quality_checks-style cell into individual ids."""
    return [part.strip() for part in re.split(r"[;,]", value or "") if part.strip()]


def _is_nonblank_str(value):
    return isinstance(value, str) and bool(value.strip())


def _shown(raw):
    return raw if isinstance(raw, str) and raw.strip() else "(blank)"


def _is_iso_date(value):
    """True when value is a valid ISO calendar date formatted YYYY-MM-DD."""
    if not isinstance(value, str):
        return False
    match = ISO_DATE_RE.match(value.strip())
    if not match:
        return False
    year, month, day = (int(part) for part in match.groups())
    try:
        datetime.date(year, month, day)
    except ValueError:
        return False
    return True


def _normalize_currency_token(value):
    """Fold spacing/hyphen/case variants of special currency words for comparison."""
    return re.sub(r"[\s\-]+", "_", str(value).strip().casefold())


def _iter_json_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _iter_json_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_json_strings(child)


def _read_csv(path):
    """Return (header, rows, error). Rows are dicts keyed by stripped header names."""
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            raw_rows = list(csv.reader(handle))
    except (OSError, csv.Error, UnicodeDecodeError) as exc:
        return None, [], f"file could not be read as CSV: {exc}"
    if not raw_rows:
        return None, [], "file is empty (no header row)"
    header = [name.strip() for name in raw_rows[0]]
    rows = []
    for raw in raw_rows[1:]:
        if not any(cell.strip() for cell in raw):
            continue
        rows.append(
            {header[i]: (raw[i].strip() if i < len(raw) else "") for i in range(len(header))}
        )
    return header, rows, None


def _load_json(path):
    """Return (data, error)."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return None, f"file could not be read: {exc}"
    except UnicodeDecodeError as exc:
        return None, f"file is not valid UTF-8 text: {exc}"
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, f"file is not valid JSON: {exc}"


def _safe_scan(project_dir, max_files, max_depth):
    """Deterministic bounded traversal for the heuristic safety scan.

    Returns (files, skipped, limit_hit): files is a list of
    (path, rel_posix, size) for regular files reached WITHOUT following
    symbolic links or Windows reparse-point junctions, so the scan never reads
    outside the project root and cannot recurse through link cycles. skipped is
    a list of (rel_posix, code) for entries deliberately not read or
    uninspectable, and limit_hit is a code when a scan cap stopped the walk
    early (None otherwise). Directory order is sorted for determinism.
    """
    files = []
    skipped = []
    state = {"processed": 0, "limit_hit": None}

    def visit(dir_path, rel_prefix, depth):
        try:
            with os.scandir(dir_path) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError:
            skipped.append((rel_prefix or ".", "SCAN_DIR_UNREADABLE"))
            return
        for entry in entries:
            if state["processed"] >= max_files:
                state["limit_hit"] = "SCAN_LIMIT_FILES"
                return
            rel = f"{rel_prefix}/{entry.name}" if rel_prefix else entry.name
            state["processed"] += 1
            try:
                if entry.is_symlink():
                    skipped.append((rel, "SCAN_SKIPPED_LINK"))
                    continue
                info = entry.stat(follow_symlinks=False)
                if getattr(info, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT:
                    skipped.append((rel, "SCAN_SKIPPED_JUNCTION"))
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if depth >= max_depth:
                        skipped.append((rel, "SCAN_LIMIT_DEPTH"))
                        continue
                    visit(entry.path, rel, depth + 1)
                elif entry.is_file(follow_symlinks=False):
                    files.append((Path(entry.path), rel, info.st_size))
                else:
                    skipped.append((rel, "SCAN_SKIPPED_SPECIAL"))
            except OSError:
                skipped.append((rel, "SCAN_ENTRY_UNREADABLE"))

    visit(str(project_dir), "", 0)
    return files, skipped, state["limit_hit"]


class _Validator:
    """Collects deterministic findings for one project directory."""

    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self.issues = []
        self.warnings = []
        self.ledger_ids = None        # None means the ledger is unavailable
        self.source_keys = None       # source_id and object_name values
        self.metric_catalog_ids = None
        self.metric_catalog_rows = None
        self.quality_rule_ids = None
        self.project_gatekeep = False  # project status is ready/human_validated
        self.project_approval = None   # analysis-spec human_approval object or None
        self.project_approval_complete = False
        self.human_validated_sites = []  # (rel, where) excluding analysis-spec itself
        self.validated_keys = set()    # artifacts whose validator actually ran
        self.registry_rel = {}         # registry key -> declared rel path

    # -- finding helpers ---------------------------------------------------

    def issue(self, code, path, message):
        self.issues.append({"code": code, "path": path, "message": message})

    def warn(self, code, path, message):
        self.warnings.append({"code": code, "path": path, "message": message})

    def rel(self, path):
        try:
            return Path(path).relative_to(self.project_dir).as_posix()
        except ValueError:
            return str(path)

    # -- shared checks -----------------------------------------------------

    def check_headers(self, rel, filename, header):
        required = CSV_REQUIRED_HEADERS[filename]
        missing = [name for name in required if name not in header]
        if missing:
            self.issue(
                "CSV_HEADER_MISSING", rel,
                f"missing required column(s): {', '.join(missing)} "
                f"(extra columns are allowed)",
            )

    def check_lifecycle(self, rel, raw, where):
        """Validate a lifecycle status; returns True when it is 'human_validated'."""
        value = raw.strip() if isinstance(raw, str) else ""
        if value in PROHIBITED_STATES:
            self.issue(
                "STATUS_PROHIBITED", rel,
                f"{where}: status '{value}' is prohibited; "
                f"use one of {', '.join(sorted(LIFECYCLE_STATES))}",
            )
            return False
        if value not in LIFECYCLE_STATES:
            self.issue(
                "STATE_INVALID", rel,
                f"{where}: status {_shown(raw)} is not a lifecycle state "
                f"(allowed: {', '.join(sorted(LIFECYCLE_STATES))})",
            )
            return False
        return value == "human_validated"

    def check_evidence_review(self, rel, raw, where):
        value = raw.strip() if isinstance(raw, str) else ""
        if value not in EVIDENCE_REVIEW_STATES:
            self.issue(
                "EVIDENCE_REVIEW_STATE_INVALID", rel,
                f"{where}: evidence review state {_shown(raw)} is not allowed "
                f"(allowed: {', '.join(sorted(EVIDENCE_REVIEW_STATES))}); this is "
                f"separate from the lifecycle states",
            )

    def check_glossary_review(self, rel, raw, where):
        value = raw.strip() if isinstance(raw, str) else ""
        if value not in GLOSSARY_REVIEW_STATES:
            self.issue(
                "GLOSSARY_STATE_INVALID", rel,
                f"{where}: glossary review status {_shown(raw)} is not allowed "
                f"(allowed: {', '.join(sorted(GLOSSARY_REVIEW_STATES))}); this is "
                f"separate from the lifecycle states",
            )

    def check_dialect(self, rel, dialect, validation, where):
        name = dialect.strip().lower() if isinstance(dialect, str) else ""
        flag = validation.strip() if isinstance(validation, str) else ""
        if flag not in DIALECT_VALIDATION_VALUES:
            self.issue(
                "STATE_INVALID", rel,
                f"{where}: dialect_validation {_shown(validation)} must be exactly "
                f"'{DIALECT_UNVALIDATED}' or 'DIALECT_VALIDATED'",
            )
        elif (not name or name not in KNOWN_DIALECTS) and flag != DIALECT_UNVALIDATED:
            self.issue(
                "DIALECT_UNVALIDATED_REQUIRED", rel,
                f"{where}: dialect {_shown(dialect)} is blank or not recognized, "
                f"so dialect_validation must be '{DIALECT_UNVALIDATED}'",
            )

    def require_text(self, rel, container, key, code, where):
        if not _is_nonblank_str(container.get(key)):
            self.issue(code, rel, f"{where}: '{key}' must be a non-blank string")
            return False
        return True

    def require_schema_version(self, rel, spec, where):
        if spec.get("schema_version") != SCHEMA_VERSION:
            self.issue(
                "SCHEMA_VERSION_INVALID", rel,
                f"{where}: 'schema_version' must be the string "
                f"'{SCHEMA_VERSION}' (got {spec.get('schema_version')!r})",
            )

    def record_human_validated(self, rel, where):
        self.human_validated_sites.append((rel, where))

    @staticmethod
    def _approval_complete(approval):
        return (
            isinstance(approval, dict)
            and _is_nonblank_str(approval.get("name"))
            and _is_nonblank_str(approval.get("date"))
        )

    def check_project_approval(self, rel, approval, incomplete_message):
        """Validate a required approval object: presence and ISO date format."""
        if not self._approval_complete(approval):
            self.issue("HUMAN_APPROVAL_INCOMPLETE", rel, incomplete_message)
            return False
        if not _is_iso_date(approval.get("date")):
            self.issue(
                "HUMAN_APPROVAL_DATE_INVALID", rel,
                f"{rel}: human_approval.date {_shown(approval.get('date'))} must "
                f"be a valid ISO calendar date (YYYY-MM-DD)",
            )
            return False
        return True

    def check_unique_ids(self, rel, values, label):
        seen = set()
        unique = []
        for value in values:
            if not value.strip():
                self.issue("ID_BLANK", rel, f"{label}: id is blank")
                continue
            if value in seen:
                self.issue("ID_DUPLICATE", rel, f"{label}: id '{value}' is duplicated")
                continue
            seen.add(value)
            unique.append(value)
        return unique

    def check_evidence_cell(self, rel, raw_value, where):
        if self.ledger_ids is None:
            return
        for evidence_id in _split_ids(raw_value):
            if evidence_id not in self.ledger_ids:
                self.issue(
                    "EVIDENCE_REF_BROKEN", rel,
                    f"{where}: evidence id '{evidence_id}' is not defined in the "
                    f"evidence ledger",
                )

    def check_evidence_list(self, rel, value, where, require_nonempty=False):
        if not isinstance(value, list):
            self.issue(
                "JSON_FIELD_TYPE", rel, f"{where}: must be a list of evidence id strings"
            )
            return
        if require_nonempty and not value:
            self.issue(
                "EVIDENCE_REF_MISSING", rel,
                f"{where}: at least one evidence id is required",
            )
            return
        if self.ledger_ids is None:
            return
        for evidence_id in value:
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                self.issue(
                    "EVIDENCE_REF_BROKEN", rel,
                    f"{where}: evidence ids must be non-blank strings",
                )
            elif evidence_id.strip() not in self.ledger_ids:
                self.issue(
                    "EVIDENCE_REF_BROKEN", rel,
                    f"{where}: evidence id '{evidence_id}' is not defined in the "
                    f"evidence ledger",
                )

    def check_placeholders(self, rel, texts, gate_label):
        tokens = sorted(
            {
                match.group(0)
                for text in texts
                for match in TEMPLATE_PLACEHOLDER_RE.finditer(text or "")
            }
        )
        if tokens:
            self.issue(
                "TEMPLATE_PLACEHOLDER_PRESENT", rel,
                f"template placeholder token(s) remain: {', '.join(tokens)}; "
                f"replace them before {gate_label}",
            )

    def _doc_strings_for_placeholder_scan(self, spec):
        return list(_iter_json_strings(spec))

    # -- manifest ----------------------------------------------------------

    def check_analysis_spec(self, spec):
        rel = ANALYSIS_SPEC_FILENAME
        self.require_schema_version(rel, spec, "analysis-spec")

        workstreams = spec.get("enabled_workstreams")
        enabled = []
        seen_workstreams = set()
        if not isinstance(workstreams, list):
            self.issue(
                "JSON_FIELD_TYPE", rel,
                "'enabled_workstreams' must be a list of workstream names",
            )
        else:
            for name in workstreams:
                if not _is_nonblank_str(name):
                    self.issue(
                        "JSON_FIELD_TYPE", rel,
                        "'enabled_workstreams' entries must be non-blank strings",
                    )
                elif name not in WORKSTREAMS:
                    self.issue(
                        "WORKSTREAM_UNKNOWN", rel,
                        f"unknown workstream '{name}' "
                        f"(known: {', '.join(WORKSTREAMS)})",
                    )
                elif name in seen_workstreams:
                    self.issue(
                        "WORKSTREAM_DUPLICATE", rel,
                        f"workstream '{name}' is listed more than once in "
                        f"'enabled_workstreams'",
                    )
                else:
                    seen_workstreams.add(name)
                    enabled.append(name)
        if isinstance(workstreams, list) and not enabled:
            self.warn(
                "WORKSTREAMS_EMPTY", rel,
                "no valid workstreams are enabled; only the always-on artifacts "
                "are required",
            )

        project = spec.get("project")
        if not isinstance(project, dict):
            self.issue("JSON_FIELD_TYPE", rel, "'project' must be an object")
        else:
            for key in ("id", "title"):
                if not _is_nonblank_str(project.get(key)):
                    self.issue(
                        "PROJECT_FIELD_MISSING", rel,
                        f"'project.{key}' must be a non-blank string",
                    )

        status_raw = spec.get("status")
        is_validated = self.check_lifecycle(rel, status_raw, "analysis-spec")
        self.project_gatekeep = (
            isinstance(status_raw, str) and status_raw.strip() in GATEKEEP_STATES
        )
        approval = spec.get("human_approval")
        self.project_approval = approval if isinstance(approval, dict) else None
        self.project_approval_complete = self._approval_complete(approval)
        if is_validated:
            self.check_project_approval(
                rel, approval,
                "analysis-spec: status 'human_validated' requires non-blank "
                "human_approval.name and human_approval.date (the tool records "
                "presence only; it cannot verify who entered them)",
            )

        for key in ("business_question", "intended_decision", "environment",
                    "data_classification"):
            self.require_text(rel, spec, key, "REQUIRED_FIELD_MISSING", "analysis-spec")

        time_context = spec.get("time_context")
        if not isinstance(time_context, dict):
            self.issue("JSON_FIELD_TYPE", rel, "'time_context' must be an object")
        else:
            for key in ("as_of_date", "timezone", "cutoff"):
                if key not in time_context:
                    self.issue(
                        "REQUIRED_FIELD_MISSING", rel,
                        f"'time_context.{key}' is required",
                    )
                elif self.project_gatekeep and not _is_nonblank_str(time_context.get(key)):
                    self.issue(
                        "REQUIRED_FIELD_MISSING", rel,
                        f"'time_context.{key}' must be non-blank once the project "
                        f"status is one of {', '.join(sorted(GATEKEEP_STATES))}",
                    )

        owners = spec.get("owners")
        if not isinstance(owners, dict):
            self.issue("JSON_FIELD_TYPE", rel, "'owners' must be an object")
        else:
            for key in ("business", "data", "reviewer"):
                if key not in owners:
                    self.issue(
                        "REQUIRED_FIELD_MISSING", rel, f"'owners.{key}' is required"
                    )
                elif self.project_gatekeep and not _is_nonblank_str(owners.get(key)):
                    self.issue(
                        "REQUIRED_FIELD_MISSING", rel,
                        f"'owners.{key}' must be non-blank once the project status "
                        f"is one of {', '.join(sorted(GATEKEEP_STATES))}",
                    )

        platform = spec.get("platform")
        if not isinstance(platform, dict):
            self.issue(
                "JSON_FIELD_TYPE", rel,
                "'platform' must be an object with 'dialect' and "
                "'dialect_validation'",
            )
        else:
            for key in ("dialect", "dialect_validation"):
                if key not in platform:
                    self.issue(
                        "REQUIRED_FIELD_MISSING", rel,
                        f"'platform.{key}' is required",
                    )
            self.check_dialect(
                rel, platform.get("dialect"), platform.get("dialect_validation"),
                "platform",
            )

        if self.project_gatekeep:
            self.check_placeholders(
                rel, self._doc_strings_for_placeholder_scan(spec), _shown(status_raw)
            )

        artifacts = spec.get("artifacts")
        if not isinstance(artifacts, dict):
            self.issue("JSON_FIELD_TYPE", rel, "'artifacts' must be an object")
            artifacts = {}
        return enabled, artifacts

    def artifact_targets(self, artifacts):
        """Return {key: (rel, abs_path)} for declared artifacts that exist inside
        the project directory; reports declaration problems."""
        base = self.project_dir.resolve()
        targets = {}
        for key in sorted(artifacts):
            known = set(ALWAYS_ARTIFACTS) | {
                k for keys in WORKSTREAM_ARTIFACTS.values() for k in keys
            }
            if key not in known:
                continue
            declared = artifacts.get(key)
            if not isinstance(declared, str):
                self.issue(
                    "ARTIFACT_PATH_TYPE", ANALYSIS_SPEC_FILENAME,
                    f"artifacts.{key} must be a string path (empty string means "
                    f"the artifact is not used)",
                )
                continue
            if not declared.strip():
                continue
            abs_path = self.project_dir / declared
            try:
                resolved = abs_path.resolve()
            except OSError:
                resolved = None
            if resolved is None or not resolved.is_relative_to(base):
                self.issue(
                    "ARTIFACT_PATH_ESCAPES", ANALYSIS_SPEC_FILENAME,
                    f"artifacts.{key} path '{declared}' resolves outside the "
                    f"project directory and was not validated",
                )
                continue
            # Resolve against the real (long-form) project path so relative
            # names stay stable even when the caller passes an 8.3-style path.
            rel = resolved.relative_to(base).as_posix()
            if not resolved.is_file():
                self.issue(
                    "ARTIFACT_FILE_MISSING", rel,
                    f"artifact '{key}' is declared as '{declared}' but the file "
                    f"does not exist",
                )
                continue
            targets[key] = (rel, resolved)
        return targets

    def check_required_artifacts(self, enabled, artifacts):
        required = set(ALWAYS_ARTIFACTS)
        for name in enabled:
            required.update(WORKSTREAM_ARTIFACTS[name])
        # analysis_spec is the manifest file itself and needs no declaration.
        for key in sorted(required - {"analysis_spec"}):
            declared = artifacts.get(key)
            if not (_is_nonblank_str(declared) and declared.strip()):
                self.issue(
                    "ARTIFACT_NOT_DECLARED", ANALYSIS_SPEC_FILENAME,
                    f"artifact '{key}' is required by the enabled workstreams but "
                    f"artifacts.{key} is blank or missing",
                )

    # -- CSV artifacts -----------------------------------------------------

    def validate_evidence_ledger(self, rel, header, rows):
        self.check_headers(rel, "evidence-ledger.csv", header)
        ids = []
        for row_no, row in enumerate(rows, start=2):
            where = f"evidence-ledger.csv row {row_no}"
            evidence_id = row.get("evidence_id", "")
            if evidence_id.strip():
                ids.append(evidence_id)
            else:
                self.issue("ID_BLANK", rel, f"{where}: 'evidence_id' is blank")
            state = row.get("state", "").strip()
            if state not in EVIDENCE_CLAIM_STATES:
                self.issue(
                    "EVIDENCE_STATE_INVALID", rel,
                    f"{where}: claim state {_shown(row.get('state', ''))} is not "
                    f"allowed (allowed: {', '.join(sorted(EVIDENCE_CLAIM_STATES))})",
                )
            if not row.get("claim", "").strip():
                self.issue(
                    "EVIDENCE_CLAIM_MISSING", rel,
                    f"{where}: 'claim' must be a non-blank description of the "
                    f"evidence",
                )
            if not row.get("source_locator", "").strip():
                self.issue(
                    "EVIDENCE_LOCATOR_MISSING", rel,
                    f"{where}: 'source_locator' must be a checkable pointer to the "
                    f"evidence source",
                )
            confidence = row.get("confidence", "").strip()
            if confidence not in CONFIDENCE_VALUES:
                self.issue(
                    "EVIDENCE_CONFIDENCE_INVALID", rel,
                    f"{where}: confidence {_shown(row.get('confidence', ''))} is not "
                    f"allowed (allowed: {', '.join(sorted(CONFIDENCE_VALUES))})",
                )
            if not row.get("owner", "").strip():
                self.issue(
                    "EVIDENCE_OWNER_MISSING", rel,
                    f"{where}: 'owner' must name the person accountable for "
                    f"confirming the evidence",
                )
            self.check_evidence_review(
                rel, row.get("validation_state", ""), where
            )
        self.check_unique_ids(rel, ids, "evidence-ledger.csv")
        self.ledger_ids = set(ids)
        if not rows:
            self.warn(
                "EVIDENCE_LEDGER_EMPTY", rel,
                "the evidence ledger has no rows; every other artifact is expected "
                "to cite evidence ids from it",
            )

    def validate_source_inventory(self, rel, header, rows):
        self.check_headers(rel, "source-inventory.csv", header)
        ids = []
        names = []
        for row_no, row in enumerate(rows, start=2):
            where = f"source-inventory.csv row {row_no}"
            source_id = row.get("source_id", "")
            if source_id.strip():
                ids.append(source_id)
            else:
                self.issue("ID_BLANK", rel, f"{where}: 'source_id' is blank")
            object_name = row.get("object_name", "").strip()
            if object_name:
                names.append(object_name)
            object_type = row.get("object_type", "").strip()
            if object_type not in OBJECT_TYPES:
                self.issue(
                    "OBJECT_TYPE_INVALID", rel,
                    f"{where}: object_type {_shown(row.get('object_type', ''))} is "
                    f"not allowed (allowed: {', '.join(sorted(OBJECT_TYPES))})",
                )
            if self.check_lifecycle(rel, row.get("status", ""), where):
                self.record_human_validated(rel, where)
            self.check_evidence_cell(rel, row.get("evidence_ids", ""), where)
        self.check_unique_ids(rel, ids, "source-inventory.csv")
        self.source_keys = set(ids) | set(names)

    def validate_glossary(self, rel, header, rows):
        self.check_headers(rel, "glossary.csv", header)
        ids = []
        for row_no, row in enumerate(rows, start=2):
            where = f"glossary.csv row {row_no}"
            term_id = row.get("term_id", "")
            if term_id.strip():
                ids.append(term_id)
            else:
                self.issue("ID_BLANK", rel, f"{where}: 'term_id' is blank")
            self.check_glossary_review(rel, row.get("status", ""), where)
            self.check_evidence_cell(rel, row.get("evidence_ids", ""), where)
        self.check_unique_ids(rel, ids, "glossary.csv")

    def validate_metric_catalog(self, rel, header, rows):
        self.check_headers(rel, "metric-catalog.csv", header)
        ids = []
        for row_no, row in enumerate(rows, start=2):
            where = f"metric-catalog.csv row {row_no}"
            metric_id = row.get("metric_id", "")
            if metric_id.strip():
                ids.append(metric_id)
            else:
                self.issue("ID_BLANK", rel, f"{where}: 'metric_id' is blank")
            aggregation = row.get("aggregation_behavior", "").strip()
            if aggregation and aggregation not in AGGREGATION_BEHAVIORS:
                self.issue(
                    "AGGREGATION_INVALID", rel,
                    f"{where}: aggregation_behavior {_shown(row.get('aggregation_behavior', ''))} "
                    f"is not allowed "
                    f"(allowed: {', '.join(sorted(AGGREGATION_BEHAVIORS))})",
                )
            currency = row.get("currency", "").strip()
            if currency and not (
                currency in METRIC_CURRENCY_SPECIAL or ISO_CURRENCY_RE.match(currency)
            ):
                self.issue(
                    "CURRENCY_FORMAT_INVALID", rel,
                    f"{where}: currency '{currency}' should be an ISO 4217 code, "
                    f"'mixed', 'account_currency', or 'not_applicable'",
                )
            if self.check_lifecycle(rel, row.get("status", ""), where):
                self.record_human_validated(rel, where)
            self.check_evidence_cell(rel, row.get("evidence_ids", ""), where)
        self.check_unique_ids(rel, ids, "metric-catalog.csv")
        self.metric_catalog_ids = set(ids)
        self.metric_catalog_rows = {
            row.get("metric_id", "").strip(): row for row in rows
        }

    def validate_quality_rules(self, rel, header, rows):
        self.check_headers(rel, "quality-rules.csv", header)
        ids = []
        for row_no, row in enumerate(rows, start=2):
            where = f"quality-rules.csv row {row_no}"
            rule_id = row.get("rule_id", "")
            if rule_id.strip():
                ids.append(rule_id)
            else:
                self.issue("ID_BLANK", rel, f"{where}: 'rule_id' is blank")
            dimension = row.get("quality_dimension", "").strip()
            if dimension not in QUALITY_DIMENSIONS:
                self.issue(
                    "QUALITY_DIMENSION_INVALID", rel,
                    f"{where}: quality_dimension {_shown(row.get('quality_dimension', ''))} "
                    f"is not allowed (allowed: {', '.join(sorted(QUALITY_DIMENSIONS))})",
                )
            severity = row.get("severity", "").strip()
            if severity not in QUALITY_SEVERITIES:
                self.issue(
                    "QUALITY_SEVERITY_INVALID", rel,
                    f"{where}: severity {_shown(row.get('severity', ''))} is not "
                    f"allowed (allowed: {', '.join(sorted(QUALITY_SEVERITIES))})",
                )
            status_value = row.get("status", "").strip()
            if (
                status_value in GATEKEEP_STATES
                and not row.get("threshold", "").strip()
            ):
                self.issue(
                    "QUALITY_THRESHOLD_MISSING", rel,
                    f"{where}: 'threshold' is human-owned and must be filled once "
                    f"the rule leaves draft/blocked",
                )
            if self.check_lifecycle(rel, row.get("status", ""), where):
                self.record_human_validated(rel, where)
            if not row.get("owner", "").strip():
                self.issue(
                    "QUALITY_OWNER_MISSING", rel,
                    f"{where}: 'owner' must name the accountable owner",
                )
            evidence = _split_ids(row.get("evidence_ids", ""))
            if not evidence:
                self.issue(
                    "EVIDENCE_REF_MISSING", rel,
                    f"{where}: at least one evidence id is required",
                )
            self.check_evidence_cell(rel, row.get("evidence_ids", ""), where)
        self.check_unique_ids(rel, ids, "quality-rules.csv")
        self.quality_rule_ids = set(ids)

    def validate_source_to_target(self, rel, header, rows):
        self.check_headers(rel, "source-to-target.csv", header)
        required_fields = (
            "source_object", "source_field", "target_object", "target_field",
            "target_definition", "target_logical_type", "data_classification",
        )
        ids = []
        for row_no, row in enumerate(rows, start=2):
            where = f"source-to-target.csv row {row_no}"
            mapping_id = row.get("mapping_id", "")
            if mapping_id.strip():
                ids.append(mapping_id)
            else:
                self.issue("ID_BLANK", rel, f"{where}: 'mapping_id' is blank")
            for field in required_fields:
                if not row.get(field, "").strip():
                    self.issue(
                        "MAPPING_FIELD_MISSING", rel,
                        f"{where}: '{field}' must be a non-blank string",
                    )
            if not row.get("owner", "").strip():
                self.issue(
                    "MAPPING_FIELD_MISSING", rel,
                    f"{where}: 'owner' must name the accountable owner",
                )
            if not row.get("transformation_rule", "").strip():
                self.issue(
                    "MAPPING_IMPLICIT_TRANSFORMATION", rel,
                    f"{where}: 'transformation_rule' is blank; state the rule "
                    f"explicitly (e.g. 'none - direct copy') so no implicit "
                    f"conversion is introduced",
                )
            nullable = row.get("nullable", "").strip()
            if not nullable:
                self.issue(
                    "MAPPING_FIELD_MISSING", rel,
                    f"{where}: 'nullable' must be filled (yes/no)",
                )
            elif nullable not in NULLABLE_VALUES:
                self.issue(
                    "MAPPING_NULLABLE_INVALID", rel,
                    f"{where}: 'nullable' value {_shown(row.get('nullable', ''))} is "
                    f"not recognized (use yes/no)",
                )
            if nullable in NULLABLE_FALSE_VALUES and not row.get("default_rule", "").strip():
                self.issue(
                    "MAPPING_IMPLICIT_DEFAULT", rel,
                    f"{where}: target is not nullable but 'default_rule' is blank; "
                    f"state the default or the source guarantee explicitly",
                )
            if row.get("unresolved_issue", "").strip():
                self.warn(
                    "MAPPING_UNRESOLVED_ISSUE", rel,
                    f"{where}: row still has an unresolved issue recorded",
                )
            source_ref = row.get("source_object", "").strip()
            if source_ref and self.source_keys is not None and source_ref not in self.source_keys:
                self.issue(
                    "CROSS_REF_SOURCE_UNKNOWN", rel,
                    f"{where}: source_object '{source_ref}' does not resolve to a "
                    f"source_id or object_name in the source inventory",
                )
            for rule_id in _split_ids(row.get("quality_checks", "")):
                if (
                    self.quality_rule_ids is not None
                    and rule_id not in self.quality_rule_ids
                ):
                    self.issue(
                        "CROSS_REF_QUALITY_RULE_UNKNOWN", rel,
                        f"{where}: quality_checks reference '{rule_id}' is not "
                        f"defined in quality-rules.csv",
                    )
            evidence = _split_ids(row.get("evidence_ids", ""))
            if not evidence:
                self.issue(
                    "EVIDENCE_REF_MISSING", rel,
                    f"{where}: at least one evidence id is required",
                )
            self.check_evidence_cell(rel, row.get("evidence_ids", ""), where)
            if self.check_lifecycle(rel, row.get("review_state", ""), where):
                self.record_human_validated(rel, where)
        self.check_unique_ids(rel, ids, "source-to-target.csv")

    # -- JSON artifacts ----------------------------------------------------

    def validate_model_spec(self, rel, spec):
        self.require_schema_version(rel, spec, "model-spec")
        if self.check_lifecycle(rel, spec.get("status"), "model-spec"):
            self.record_human_validated(rel, "model-spec")
        self.require_text(rel, spec, "model_id", "REQUIRED_FIELD_MISSING", "model-spec")
        self.require_text(rel, spec, "title", "REQUIRED_FIELD_MISSING", "model-spec")
        self.check_evidence_list(rel, spec.get("evidence_ids"), "model-spec.evidence_ids")
        if self._artifact_needs_placeholder_scan(spec):
            self.check_placeholders(
                rel, self._doc_strings_for_placeholder_scan(spec), "human validation"
            )

        for key in ("entities", "relationships"):
            if key not in spec:
                self.issue(
                    "REQUIRED_FIELD_MISSING", rel, f"'{key}' is required"
                )

        entities = spec.get("entities")
        if not isinstance(entities, list):
            self.issue("JSON_FIELD_TYPE", rel, "'entities' must be a list")
            entities = []
        elif not entities:
            self.warn(
                "MODEL_EMPTY", rel,
                "model-spec declares no entities; draft at least one entity or "
                "narrow the enabled workstreams",
            )
        entity_ids = []
        for index, entity in enumerate(entities, start=1):
            where = f"entities[{index}]"
            if not isinstance(entity, dict):
                self.issue("JSON_FIELD_TYPE", rel, f"{where}: must be an object")
                continue
            entity_id = entity.get("entity_id")
            if _is_nonblank_str(entity_id):
                if entity_id in entity_ids:
                    self.issue(
                        "ID_DUPLICATE", rel,
                        f"{where}: entity_id '{entity_id}' is duplicated",
                    )
                else:
                    entity_ids.append(entity_id)
            else:
                self.issue("ID_BLANK", rel, f"{where}: 'entity_id' must be a non-blank string")
            for field in ("name", "definition", "temporal_strategy", "classification"):
                if not _is_nonblank_str(entity.get(field)):
                    self.issue(
                        "MODEL_ENTITY_FIELD_MISSING", rel,
                        f"{where}: '{field}' must be a non-blank string",
                    )
            if not _is_nonblank_str(entity.get("grain")):
                self.issue(
                    "MODEL_ENTITY_GRAIN_MISSING", rel,
                    f"{where}: 'grain' must state the grain of this entity",
                )
            keys = entity.get("business_keys")
            if not isinstance(keys, list) or not keys or not all(_is_nonblank_str(k) for k in keys):
                self.issue(
                    "MODEL_ENTITY_KEYS_MISSING", rel,
                    f"{where}: 'business_keys' must be a non-empty list of key names",
                )
            self.check_evidence_list(
                rel, entity.get("evidence_ids"), f"{where}.evidence_ids",
                require_nonempty=True,
            )
            attributes = entity.get("attributes")
            if attributes is not None and not isinstance(attributes, list):
                self.issue("JSON_FIELD_TYPE", rel, f"{where}.attributes: must be a list")
            elif isinstance(attributes, list):
                for attr_index, attribute in enumerate(attributes, start=1):
                    attr_where = f"{where}.attributes[{attr_index}]"
                    if not isinstance(attribute, dict):
                        self.issue(
                            "JSON_FIELD_TYPE", rel, f"{attr_where}: must be an object"
                        )
                        continue
                    for field in ("name", "logical_type", "definition"):
                        if not _is_nonblank_str(attribute.get(field)):
                            self.issue(
                                "MODEL_ATTRIBUTE_FIELD_MISSING", rel,
                                f"{attr_where}: '{field}' must be a non-blank string",
                            )

        relationships = spec.get("relationships")
        if not isinstance(relationships, list):
            self.issue("JSON_FIELD_TYPE", rel, "'relationships' must be a list")
            relationships = []
        relationship_ids = []
        for index, relationship in enumerate(relationships, start=1):
            where = f"relationships[{index}]"
            if not isinstance(relationship, dict):
                self.issue("JSON_FIELD_TYPE", rel, f"{where}: must be an object")
                continue
            relationship_id = relationship.get("relationship_id")
            if _is_nonblank_str(relationship_id):
                if relationship_id in relationship_ids:
                    self.issue(
                        "ID_DUPLICATE", rel,
                        f"{where}: relationship_id '{relationship_id}' is duplicated",
                    )
                else:
                    relationship_ids.append(relationship_id)
            else:
                self.issue(
                    "ID_BLANK", rel,
                    f"{where}: 'relationship_id' must be a non-blank string",
                )
            for endpoint in ("from_entity", "to_entity"):
                value = relationship.get(endpoint)
                if not _is_nonblank_str(value) or value not in entity_ids:
                    self.issue(
                        "RELATIONSHIP_ENDPOINT_UNKNOWN", rel,
                        f"{where}: '{endpoint}' does not reference a declared "
                        f"entity_id in this model",
                    )
            self.check_evidence_list(
                rel, relationship.get("evidence_ids"), f"{where}.evidence_ids",
                require_nonempty=True,
            )

    def _artifact_needs_placeholder_scan(self, spec):
        if self.project_gatekeep:
            return True
        status = spec.get("status")
        return isinstance(status, str) and status.strip() in GATEKEEP_STATES

    def _check_currency_basis(self, rel, currency, where, prefix):
        """Validate a currency_basis/currency_controls object; returns (mode, currencies)."""
        mode = currency.get("mode")
        if not _is_nonblank_str(mode) or mode not in CURRENCY_MODES:
            self.issue(
                f"{prefix}_CURRENCY_MODE_INVALID", rel,
                f"{where}.mode must be one of: {', '.join(sorted(CURRENCY_MODES))}",
            )
            return mode if isinstance(mode, str) else "", []
        raw = currency.get("currencies")
        if not isinstance(raw, list):
            self.issue(
                f"{prefix}_CURRENCY_MISSING", rel,
                f"{where}.currencies must be a list of currency codes",
            )
            raw = []
        well_formed = bool(raw) and all(_is_nonblank_str(c) for c in raw)
        currencies = [str(c).strip() for c in raw if isinstance(c, str) and str(c).strip()]
        if mode in ("single_currency", "multi_currency"):
            if not raw:
                self.issue(
                    f"{prefix}_CURRENCY_MISSING", rel,
                    f"{where}.currencies must be a non-empty list of currency codes",
                )
            elif not well_formed:
                self.issue(
                    f"{prefix}_CURRENCY_MISSING", rel,
                    f"{where}.currencies entries must be non-blank strings",
                )
            else:
                if mode == "single_currency" and len(currencies) != 1:
                    self.issue(
                        f"{prefix}_CURRENCY_COUNT", rel,
                        f"{where}: mode 'single_currency' requires exactly one currency",
                    )
                if mode == "multi_currency" and len(currencies) < 2:
                    self.issue(
                        f"{prefix}_CURRENCY_INSUFFICIENT", rel,
                        f"{where}: mode 'multi_currency' requires at least 2 currencies",
                    )
                for code in currencies:
                    if not ISO_CURRENCY_RE.match(code):
                        self.issue(
                            f"{prefix}_CURRENCY_FORMAT_INVALID", rel,
                            f"{where}: currency '{code}' must be an uppercase "
                            f"3-letter ISO 4217-format code",
                        )
            if mode == "multi_currency" and not _is_nonblank_str(currency.get("conversion_rule")):
                self.issue(
                    f"{prefix}_CONVERSION_RULE_MISSING" if prefix == "QUERY"
                    else f"{prefix}_CURRENCY_CONVERSION_MISSING",
                    rel,
                    f"{where}.conversion_rule must state whether results stay "
                    f"partitioned by currency or how they are converted",
                )
        elif mode == "not_applicable" and currencies:
            self.issue(
                f"{prefix}_CURRENCY_NOT_APPLICABLE", rel,
                f"{where}: mode 'not_applicable' requires an empty currencies list",
            )
        return mode, currencies

    def check_query_metric_currency(self, rel, metric, where):
        """Enforce the query-metric currency vocabulary (format only)."""
        raw = metric.get("currency")
        token = raw.strip() if isinstance(raw, str) else ""
        if not token:
            return  # blank is reported by the non-blank field check
        if not (
            ISO_CURRENCY_RE.match(token)
            or _normalize_currency_token(token) in QUERY_METRIC_CURRENCY_SPECIAL
        ):
            self.issue(
                "QUERY_METRIC_CURRENCY_INVALID", rel,
                f"{where}: 'currency' must be an ISO 4217 code, "
                f"'account_currency', or 'not_applicable' (got '{token}')",
            )

    def check_metric_mirror(self, rel, metric, catalog_row, where):
        """Warn when a query metric drifts from its metric-catalog.csv entry."""
        mismatches = []
        for field in ("name", "unit"):
            catalog_value = catalog_row.get(field, "").strip()
            raw = metric.get(field)
            query_value = raw.strip() if isinstance(raw, str) else ""
            if (
                catalog_value
                and query_value
                and catalog_value.casefold() != query_value.casefold()
            ):
                mismatches.append(
                    f"{field} '{query_value}' differs from metric-catalog.csv "
                    f"'{catalog_value}'"
                )
        catalog_currency = _normalize_currency_token(catalog_row.get("currency", ""))
        query_currency = _normalize_currency_token(metric.get("currency") or "")
        if catalog_currency and query_currency and catalog_currency != query_currency:
            mismatches.append(
                f"currency '{str(metric.get('currency')).strip()}' differs from "
                f"metric-catalog.csv '{catalog_row.get('currency', '').strip()}'"
            )
        if mismatches:
            self.warn(
                "CROSS_REF_METRIC_MISMATCH", rel,
                f"{where}: " + "; ".join(mismatches)
                + "; align the query metric with its catalog entry or reference a "
                "different metric_id",
            )

    def validate_query_spec(self, rel, spec):
        self.require_schema_version(rel, spec, "query-spec")
        if self.check_lifecycle(rel, spec.get("status"), "query-spec"):
            self.record_human_validated(rel, "query-spec")
        self.check_dialect(
            rel, spec.get("dialect"), spec.get("dialect_validation"), "query-spec"
        )
        self.require_text(rel, spec, "query_id", "REQUIRED_FIELD_MISSING", "query-spec")
        self.require_text(
            rel, spec, "business_question", "REQUIRED_FIELD_MISSING", "query-spec"
        )
        self.require_text(
            rel, spec, "population", "REQUIRED_FIELD_MISSING", "query-spec"
        )
        self.require_text(
            rel, spec, "expected_row_behavior", "REQUIRED_FIELD_MISSING", "query-spec"
        )
        self.check_evidence_list(rel, spec.get("evidence_ids"), "query-spec.evidence_ids")
        if self._artifact_needs_placeholder_scan(spec):
            self.check_placeholders(
                rel, self._doc_strings_for_placeholder_scan(spec), "human validation"
            )

        sources = spec.get("verified_sources")
        if not isinstance(sources, list) or not sources or not all(_is_nonblank_str(s) for s in sources):
            self.issue(
                "QUERY_SOURCES_MISSING", rel,
                "'verified_sources' must be a non-empty list of source objects "
                "verified against the source inventory",
            )
        elif self.source_keys is not None:
            for index, source in enumerate(sources, start=1):
                name = str(source).strip()
                if name not in self.source_keys:
                    self.issue(
                        "CROSS_REF_SOURCE_UNKNOWN", rel,
                        f"verified_sources[{index}]: '{name}' does not resolve to a "
                        f"source_id or object_name in the source inventory",
                    )
        if not _is_nonblank_str(spec.get("result_grain")):
            self.issue(
                "QUERY_GRAIN_MISSING", rel,
                "'result_grain' must state the grain of one result row",
            )

        time_basis = spec.get("time_basis")
        if not isinstance(time_basis, dict):
            self.issue("JSON_FIELD_TYPE", rel, "'time_basis' must be an object")
        else:
            missing = [
                key for key in ("type", "timezone", "cutoff")
                if not _is_nonblank_str(time_basis.get(key))
            ]
            if missing:
                self.issue(
                    "QUERY_TIME_MISSING", rel,
                    f"'time_basis' is missing non-blank value(s): {', '.join(missing)}",
                )

        currency = spec.get("currency_basis")
        if not isinstance(currency, dict):
            self.issue("JSON_FIELD_TYPE", rel, "'currency_basis' must be an object")
        else:
            self._check_currency_basis(
                rel, currency, "currency_basis", prefix="QUERY"
            )

        for key in ("exclusions", "validation_checks"):
            value = spec.get(key)
            if value is not None and not isinstance(value, list):
                self.issue("JSON_FIELD_TYPE", rel, f"'{key}' must be a list")

        metrics = spec.get("metrics")
        if not isinstance(metrics, list):
            self.issue("JSON_FIELD_TYPE", rel, "'metrics' must be a list")
            metrics = []
        elif not metrics:
            self.warn(
                "QUERY_NO_METRICS", rel,
                "query-spec declares no metrics; draft at least one metric or "
                "narrow the enabled workstreams",
            )
        metric_ids = []
        for index, metric in enumerate(metrics, start=1):
            where = f"metrics[{index}]"
            if not isinstance(metric, dict):
                self.issue("JSON_FIELD_TYPE", rel, f"{where}: must be an object")
                continue
            metric_id = metric.get("metric_id")
            if not _is_nonblank_str(metric_id):
                self.issue("ID_BLANK", rel, f"{where}: 'metric_id' must be a non-blank string")
            else:
                if metric_id in metric_ids:
                    self.issue(
                        "ID_DUPLICATE", rel, f"{where}: metric_id '{metric_id}' is duplicated"
                    )
                metric_ids.append(metric_id)
                if (
                    self.metric_catalog_ids is not None
                    and metric_id not in self.metric_catalog_ids
                ):
                    self.issue(
                        "CROSS_REF_METRIC_UNKNOWN", rel,
                        f"{where}: metric_id '{metric_id}' is not defined in "
                        f"metric-catalog.csv",
                    )
            for key in ("name", "formula", "unit", "currency"):
                if not _is_nonblank_str(metric.get(key)):
                    self.issue(
                        "QUERY_METRIC_FIELD_MISSING", rel,
                        f"{where}: '{key}' must be a non-blank string",
                    )
            self.check_query_metric_currency(rel, metric, where)
            catalog_row = (
                self.metric_catalog_rows.get(metric_id.strip())
                if isinstance(self.metric_catalog_rows, dict) and _is_nonblank_str(metric_id)
                else None
            )
            if catalog_row is not None:
                self.check_metric_mirror(rel, metric, catalog_row, where)
            self.check_evidence_list(
                rel, metric.get("evidence_ids"), f"{where}.evidence_ids",
                require_nonempty=True,
            )

    def validate_reconciliation_plan(self, rel, spec):
        self.require_schema_version(rel, spec, "reconciliation-plan")
        if self.check_lifecycle(rel, spec.get("status"), "reconciliation-plan"):
            self.record_human_validated(rel, "reconciliation-plan")
            self.check_project_approval(
                rel, spec.get("human_approval"),
                "reconciliation-plan: status 'human_validated' requires "
                "non-blank human_approval.name and human_approval.date (the "
                "tool records presence only; it cannot verify who entered them)",
            )
        if not _is_nonblank_str(spec.get("reconciliation_id")):
            self.issue(
                "ID_BLANK", rel, "'reconciliation_id' must be a non-blank string"
            )
        self.check_evidence_list(
            rel, spec.get("evidence_ids"), "reconciliation-plan.evidence_ids"
        )
        if self._artifact_needs_placeholder_scan(spec):
            self.check_placeholders(
                rel, self._doc_strings_for_placeholder_scan(spec), "human validation"
            )
        for key, code in (
            ("source_population", "RECON_POPULATION_MISSING"),
            ("target_population", "RECON_POPULATION_MISSING"),
            ("grain", "RECON_GRAIN_MISSING"),
        ):
            self.require_text(rel, spec, key, code, "reconciliation-plan")

        keys = spec.get("matching_keys")
        if not isinstance(keys, list) or not keys or not all(_is_nonblank_str(k) for k in keys):
            self.issue(
                "RECON_KEYS_MISSING", rel,
                "'matching_keys' must be a non-empty list of column names that "
                "align source and target rows",
            )

        time_context = spec.get("time_context")
        if not isinstance(time_context, dict):
            self.issue("JSON_FIELD_TYPE", rel, "'time_context' must be an object")
        else:
            missing = [
                key for key in ("business_date", "cutoff", "timezone", "late_arrival_rule")
                if not _is_nonblank_str(time_context.get(key))
            ]
            if missing:
                self.issue(
                    "RECON_TIME_MISSING", rel,
                    f"'time_context' is missing non-blank value(s): {', '.join(missing)}",
                )

        currency = spec.get("currency_controls")
        mode, currencies = "", []
        if not isinstance(currency, dict):
            self.issue("JSON_FIELD_TYPE", rel, "'currency_controls' must be an object")
        else:
            mode, currencies = self._check_currency_basis(
                rel, currency, "currency_controls", prefix="RECON"
            )

        tolerances = spec.get("tolerances")
        if not isinstance(tolerances, dict):
            self.issue("JSON_FIELD_TYPE", rel, "'tolerances' must be an object")
            tolerances = {}
        for key in ("count_absolute", "amount_absolute", "amount_percentage"):
            value = tolerances.get(key)
            if not _is_nonblank_str(value):
                self.issue(
                    "RECON_TOLERANCE_MISSING", rel,
                    f"'tolerances.{key}' must be present as a decimal string "
                    f"(e.g. \"0.00\")",
                )
            elif not DECIMAL_STRING_RE.match(value.strip()):
                self.issue(
                    "RECON_TOLERANCE_FORMAT", rel,
                    f"'tolerances.{key}' must be a plain decimal string "
                    f"(e.g. \"0.00\"), got '{value}'",
                )

        controls = spec.get("controls")
        if not isinstance(controls, list):
            self.issue("JSON_FIELD_TYPE", rel, "'controls' must be a list")
            controls = []
        elif not controls:
            self.issue(
                "RECON_CONTROLS_MISSING", rel,
                "at least one reconciliation control is required",
            )
        for index, control in enumerate(controls, start=1):
            where = f"controls[{index}]"
            if not isinstance(control, dict):
                self.issue("JSON_FIELD_TYPE", rel, f"{where}: must be an object")
                continue
            control_id = control.get("control_id")
            if not _is_nonblank_str(control_id):
                self.issue("ID_BLANK", rel, f"{where}: 'control_id' must be a non-blank string")
            for key in ("type", "description"):
                if not _is_nonblank_str(control.get(key)):
                    self.issue(
                        "CONTROL_FIELD_MISSING", rel,
                        f"{where}: '{key}' must be a non-blank string",
                    )
            group_by = control.get("group_by")
            if not isinstance(group_by, list):
                self.issue("JSON_FIELD_TYPE", rel, f"{where}.group_by: must be a list")
                group_by = []
            # Control type is free text (not a contract enum), so classify it
            # case-insensitively for the monetary grouping heuristic only.
            control_type = str(control.get("type") or "").strip().lower()
            if mode == "multi_currency" and control_type in MONETARY_CONTROL_TYPES:
                if not group_by:
                    self.issue(
                        "CONTROL_FIELD_MISSING", rel,
                        f"{where}.group_by: monetary controls in multi_currency "
                        f"mode must be grouped (include a currency field such as "
                        f"'currency_code')",
                    )
                elif not any(
                    isinstance(item, str) and CURRENCY_FIELD_RE.search(item)
                    for item in group_by
                ):
                    self.issue(
                        "RECON_CURRENCY_GROUPING", rel,
                        f"{where}.group_by: monetary controls in multi_currency "
                        f"mode must group by a currency field (case-insensitive "
                        f"'currency' or 'ccy', e.g. 'currency_code'), not by a "
                        f"currency value",
                    )
            self.check_evidence_list(
                rel, control.get("evidence_ids"), f"{where}.evidence_ids",
                require_nonempty=True,
            )

        exception_management = spec.get("exception_management")
        if not isinstance(exception_management, dict):
            self.issue(
                "JSON_FIELD_TYPE", rel, "'exception_management' must be an object"
            )
        else:
            missing = [
                key for key in ("owner", "workflow", "evidence_retention")
                if not _is_nonblank_str(exception_management.get(key))
            ]
            if missing:
                self.issue(
                    "RECON_EXCEPTION_MISSING", rel,
                    f"'exception_management' is missing non-blank value(s): "
                    f"{', '.join(missing)}",
                )

    # -- review summary ------------------------------------------------------

    def validate_review_summary(self, rel, path):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            self.issue("FILE_READ_FAILED", rel, f"file could not be read: {exc}")
            return
        lines = {line.strip() for line in text.splitlines()}
        for heading in REVIEW_SUMMARY_HEADINGS:
            if heading not in lines:
                self.issue(
                    "REVIEW_HEADING_MISSING", rel,
                    f"required heading '{heading}' is missing; keep the contract "
                    f"headings verbatim",
                )
        if self.project_gatekeep:
            self.check_placeholders(rel, [text], "human validation")

    # -- safety heuristic --------------------------------------------------

    def _scan_single_file(self, path, rel, size):
        """Stream one regular file in bounded chunks with overlap and scan it."""
        try:
            handle = path.open("rb")
        except OSError:
            self.warn(
                "SCAN_UNREADABLE", rel,
                "file could not be read during the safety scan (heuristic scan, "
                "not a complete PII scanner)",
            )
            return
        found_secret = found_uri = found_account = False
        truncated = False
        consumed = 0
        try:
            with handle:
                window = handle.read(SCAN_CHUNK_BYTES)
                if b"\x00" in window[:8192]:
                    return  # binary file
                consumed = len(window)
                while True:
                    text = window.decode("utf-8", errors="ignore")
                    if not found_secret:
                        for match in SECRET_ASSIGN_RE.finditer(text):
                            if PLACEHOLDER_VALUE_RE.search(match.group(2)):
                                continue
                            found_secret = True
                            break
                    if not found_uri:
                        for match in CONN_URI_CREDS_RE.finditer(text):
                            if PLACEHOLDER_VALUE_RE.search(match.group(0)):
                                continue
                            found_uri = True
                            break
                    if not found_account and ACCOUNT_LIKE_RE.search(text):
                        found_account = True
                    if consumed >= MAX_SCAN_BYTES:
                        truncated = size > consumed
                        break
                    chunk = handle.read(SCAN_CHUNK_BYTES)
                    if not chunk:
                        break
                    window = window[-SCAN_OVERLAP_BYTES:] + chunk
                    consumed += len(chunk)
        except OSError:
            self.warn(
                "SCAN_UNREADABLE", rel,
                "file could not be read during the safety scan (heuristic scan, "
                "not a complete PII scanner)",
            )
            return
        if truncated:
            self.warn(
                "SCAN_TRUNCATED", rel,
                f"file exceeds the {MAX_SCAN_BYTES} byte scan cap; only the first "
                f"{consumed} byte(s) were checked (heuristic scan, not a complete "
                f"PII scanner)",
            )
        if found_secret:
            self.issue(
                "SUSPECTED_SECRET", rel,
                "possible credential assignment; the matched value is "
                "intentionally not shown. Remove credentials from project "
                "files. (Heuristic scan, not a complete PII scanner.)",
            )
        if found_uri:
            self.issue(
                "SUSPECTED_SECRET", rel,
                "possible connection URI with embedded credentials; the "
                "matched value is intentionally not shown. (Heuristic scan, "
                "not a complete PII scanner.)",
            )
        if found_account:
            self.issue(
                "SUSPECTED_ACCOUNT_NUMBER", rel,
                "possible 13-19 digit account or card-like number sequence; "
                "the matched value is intentionally not shown. Replace it "
                "with a synthetic identifier. (Heuristic scan, not a "
                "complete PII scanner.)",
            )

    def scan_for_secrets(self):
        """Heuristic scan for obvious secrets and account-like numbers.

        Streams regular files inside the project in bounded chunks with overlap,
        up to MAX_SCAN_BYTES bytes per file. The traversal never follows
        symbolic links or Windows reparse-point junctions, never reads outside
        the project directory, and is bounded by MAX_SCAN_FILES/MAX_SCAN_DEPTH,
        so it cannot recurse through link cycles or escape the project root.
        Anything deliberately skipped or unreadable produces a deterministic
        SCAN_* warning. Matched values are never echoed; this is a heuristic,
        not a complete PII scanner.
        """
        files, skipped, limit_hit = _safe_scan(
            self.project_dir, MAX_SCAN_FILES, MAX_SCAN_DEPTH
        )
        skip_messages = {
            "SCAN_SKIPPED_LINK": "symbolic link not followed by the safety scan",
            "SCAN_SKIPPED_JUNCTION": "reparse-point junction not followed by the safety scan",
            "SCAN_SKIPPED_SPECIAL": "non-regular file not read by the safety scan",
            "SCAN_DIR_UNREADABLE": "directory could not be listed during the safety scan",
            "SCAN_ENTRY_UNREADABLE": "entry could not be inspected during the safety scan",
            "SCAN_LIMIT_DEPTH": "scan depth limit reached; this directory was not checked",
            "SCAN_LIMIT_FILES": "scan entry limit reached; this entry was not checked",
        }
        for rel, code in skipped:
            self.warn(
                code, rel,
                skip_messages.get(code, "entry skipped by the safety scan")
                + " (heuristic scan, not a complete PII scanner)",
            )
        if limit_hit:
            self.warn(
                "SCAN_LIMIT_FILES", ".",
                f"the project exceeds {MAX_SCAN_FILES} entries; the safety scan "
                f"stopped early and some files were not checked (heuristic scan, "
                f"not a complete PII scanner)",
            )
        for path, rel, size in files:
            self._scan_single_file(path, rel, size)

    # -- orchestration -----------------------------------------------------

    def _dispatch_artifact(self, key, rel, path):
        if key in REGISTRY_KEYS:
            self.registry_rel[key] = rel
        ok = True
        if key == "evidence_ledger":
            header, rows, error = _read_csv(path)
            if error:
                self.issue("CSV_READ_FAILED", rel, error)
                ok = False  # registry unavailable: dependent checks are skipped
            else:
                self.validate_evidence_ledger(rel, header or [], rows)
        elif key == "source_inventory":
            ok = self._csv_artifact(rel, path, "source-inventory.csv", self.validate_source_inventory)
        elif key == "quality_rules":
            ok = self._csv_artifact(rel, path, "quality-rules.csv", self.validate_quality_rules)
        elif key == "metric_catalog":
            ok = self._csv_artifact(rel, path, "metric-catalog.csv", self.validate_metric_catalog)
        elif key == "glossary":
            ok = self._csv_artifact(rel, path, "glossary.csv", self.validate_glossary)
        elif key == "source_to_target":
            ok = self._csv_artifact(rel, path, "source-to-target.csv", self.validate_source_to_target)
        elif key == "model_spec":
            ok = self._json_artifact(rel, path, self.validate_model_spec)
        elif key == "query_spec":
            ok = self._json_artifact(rel, path, self.validate_query_spec)
        elif key == "reconciliation_plan":
            ok = self._json_artifact(rel, path, self.validate_reconciliation_plan)
        elif key == "review_summary":
            self.validate_review_summary(rel, path)
        # analysis_spec needs no content validation here
        if ok:
            self.validated_keys.add(key)

    def _csv_artifact(self, rel, path, filename, validator):
        header, rows, error = _read_csv(path)
        if error:
            self.issue("CSV_READ_FAILED", rel, error)
            return False
        validator(rel, header or [], rows)
        return True

    def _json_artifact(self, rel, path, validator):
        spec, error = _load_json(path)
        if error:
            self.issue("JSON_PARSE", rel, error)
            return False
        if not isinstance(spec, dict):
            self.issue(
                "JSON_ROOT_NOT_OBJECT", rel, "root of the JSON document must be an object"
            )
            return False
        validator(rel, spec)
        return True

    def _warn_skipped_cross_refs(self):
        """Report registries that could not be validated once, deterministically."""
        for attr, key, label, dependents in REGISTRY_CROSS_REFS:
            if getattr(self, attr) is None and any(
                dep in self.validated_keys for dep in dependents
            ):
                self.warn(
                    "CROSS_REF_SKIPPED", self.registry_rel.get(key, label),
                    f"{label} could not be validated, so cross-reference checks "
                    f"against it were skipped for this run",
                )

    def run(self):
        spec_path = self.project_dir / ANALYSIS_SPEC_FILENAME
        if not spec_path.is_file():
            raise _ConfigError(f"analysis spec not found: {spec_path}")
        spec, error = _load_json(spec_path)
        if error:
            raise _ConfigError(f"{ANALYSIS_SPEC_FILENAME}: {error}")
        if not isinstance(spec, dict):
            raise _ConfigError(f"{ANALYSIS_SPEC_FILENAME}: root must be a JSON object")

        enabled, artifacts = self.check_analysis_spec(spec)
        self.check_required_artifacts(enabled, artifacts)
        targets = self.artifact_targets(artifacts)

        # Dependency order: registries (ledger, sources, quality rules, metric
        # catalog) are populated before the artifacts that reference them.
        order = (
            "evidence_ledger",
            "source_inventory",
            "quality_rules",
            "metric_catalog",
            "glossary",
            "source_to_target",
            "model_spec",
            "query_spec",
            "reconciliation_plan",
            "review_summary",
        )
        for key in order:
            if key in targets:
                rel, path = targets[key]
                self._dispatch_artifact(key, rel, path)

        self._warn_skipped_cross_refs()

        # Project-level human approval gate for any human_validated occurrence.
        if self.human_validated_sites:
            if not self.project_approval_complete:
                self.issue(
                    "HUMAN_APPROVAL_INCOMPLETE", ANALYSIS_SPEC_FILENAME,
                    "artifact(s) marked 'human_validated' "
                    f"({', '.join(sorted({site[0] for site in self.human_validated_sites}))}) "
                    "require project-level human_approval.name and human_approval.date "
                    "in analysis-spec.json (the tool records presence only; it cannot "
                    "verify who entered them)",
                )
            elif not _is_iso_date((self.project_approval or {}).get("date")):
                self.issue(
                    "HUMAN_APPROVAL_DATE_INVALID", ANALYSIS_SPEC_FILENAME,
                    f"analysis-spec: human_approval.date "
                    f"{_shown((self.project_approval or {}).get('date'))} must be a "
                    f"valid ISO calendar date (YYYY-MM-DD)",
                )

        self.scan_for_secrets()

        self.issues.sort(key=lambda f: (f["path"], f["code"], f["message"]))
        self.warnings.sort(key=lambda f: (f["path"], f["code"], f["message"]))
        status = "issues" if self.issues else ("warnings" if self.warnings else "clean")
        return {
            "project_dir": str(self.project_dir),
            "status": status,
            "issues": self.issues,
            "warnings": self.warnings,
            "summary": {
                "issue_count": len(self.issues),
                "warning_count": len(self.warnings),
            },
        }


def validate_project(project_dir):
    """Validate one project directory. Raises _ConfigError for exit-2 inputs."""
    return _Validator(project_dir).run()


def render_human(report):
    lines = [
        f"Project: {report['project_dir']}",
        f"Status: {report['status'].upper()} "
        f"({report['summary']['issue_count']} issue(s), "
        f"{report['summary']['warning_count']} warning(s))",
    ]
    for label, findings in (("ISSUES", report["issues"]), ("WARNINGS", report["warnings"])):
        if not findings:
            continue
        lines.append("")
        lines.append(f"{label}:")
        for finding in findings:
            lines.append(f"  [{finding['code']}] {finding['path']}: {finding['message']}")
    if not report["issues"] and not report["warnings"]:
        lines.append("No findings. Structural validation passed.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="validate_artifacts.py",
        description="Structural validator for banking data analytics projects. "
        "Checks artifact presence, shape, vocabularies, references, and internal "
        "consistency only. This is not a business, compliance, or PII "
        "certification, and the secret/account heuristic is not a complete PII "
        "scanner. Human-approval checks verify field presence, not authorship.",
    )
    parser.add_argument("project_dir", type=Path, help="project directory to validate")
    parser.add_argument(
        "--json", action="store_true", dest="as_json",
        help="emit the machine-readable JSON report instead of human-readable text",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="treat warnings as failures for the exit code",
    )
    args = parser.parse_args(argv)

    if not args.project_dir.is_dir():
        print(f"error: project directory not found: {args.project_dir}", file=sys.stderr)
        return 2
    try:
        report = validate_project(args.project_dir)
    except _ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_human(report))

    if report["summary"]["issue_count"]:
        return 1
    if report["summary"]["warning_count"] and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
