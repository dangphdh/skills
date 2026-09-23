#!/usr/bin/env python3
"""init_project.py - scaffold a banking data analytics project from skill templates.

Copies the template artifacts for the requested workstreams into a fresh
destination directory and fills the project manifest (analysis-spec.json) and
the identity placeholders (PROJECT_ID / PROJECT_TITLE) in review-summary.md.
Draft-and-validate only: no database, network, cloud, or BI connectivity is
used or created, and no credentials or .env files are ever written.

Usage:
  python init_project.py DEST --project-id ID --title TITLE \
      --workstreams {domain-modeling,product-discovery,data-mining,quality-reconciliation} [one or more]

Artifacts per workstream (always copied: analysis-spec.json, review-summary.md):
  domain-modeling         evidence-ledger, source-inventory, glossary, model-spec
  product-discovery       evidence-ledger, source-inventory, glossary, model-spec
  data-mining             evidence-ledger, source-inventory, query-spec, metric-catalog
  quality-reconciliation  evidence-ledger, source-inventory, source-to-target,
                          quality-rules, reconciliation-plan
Duplicated artifacts across workstreams are copied once, and repeated
workstream names are deduplicated keeping first-seen order. When data-mining is
enabled an empty sql/ directory is created for ad hoc queries.

The scaffold is built in a temporary sibling directory and moved into place only
once complete. A failure mid-run removes the temporary directory and leaves the
destination nonexistent (or exactly the empty directory the caller provided), so
a failed run can simply be retried; pre-existing content is never deleted or
overwritten. The destination must not exist or must be an empty directory.
Paths for artifacts not enabled by any workstream are left as empty strings in
analysis-spec.json.

Exit codes: 0 success, 2 input or filesystem errors.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

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

ARTIFACT_TEMPLATE_FILES = {
    "analysis_spec": "analysis-spec.json",
    "evidence_ledger": "evidence-ledger.csv",
    "source_inventory": "source-inventory.csv",
    "glossary": "glossary.csv",
    "model_spec": "model-spec.json",
    "query_spec": "query-spec.json",
    "metric_catalog": "metric-catalog.csv",
    "source_to_target": "source-to-target.csv",
    "quality_rules": "quality-rules.csv",
    "reconciliation_plan": "reconciliation-plan.json",
    "review_summary": "review-summary.md",
}

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates"

STAGING_PREFIX = ".init_project-staging-"


def dedupe_workstreams(workstreams):
    """Return workstreams with duplicates removed, preserving first-seen order."""
    deduped = []
    for name in workstreams:
        if name not in deduped:
            deduped.append(name)
    return deduped


def resolve_artifact_paths(workstreams):
    """Return {artifact_key: destination_filename} for the given workstreams."""
    keys = set(ALWAYS_ARTIFACTS)
    for name in workstreams:
        keys.update(WORKSTREAM_ARTIFACTS[name])
    return {key: ARTIFACT_TEMPLATE_FILES[key] for key in sorted(keys)}


def fill_analysis_spec(spec, project_id, title, workstreams, artifact_paths):
    """Fill project identity, workstreams, and artifact paths in the manifest."""
    spec["project"]["id"] = project_id
    spec["project"]["title"] = title
    spec["enabled_workstreams"] = list(workstreams)
    artifacts = spec.setdefault("artifacts", {})
    # analysis_spec is the manifest file itself and stays out of the artifacts map.
    for key in ARTIFACT_TEMPLATE_FILES:
        if key == "analysis_spec":
            continue
        artifacts[key] = artifact_paths.get(key, "")
    return spec


def fill_review_summary(text, project_id, title):
    """Replace the review-summary template identity placeholders."""
    return text.replace("PROJECT_TITLE", title).replace("PROJECT_ID", project_id)


def build_project(dest, project_id, title, workstreams, templates_dir=TEMPLATES_DIR):
    """Scaffold the project atomically. Returns the list of created paths.

    Raises OSError/ValueError on input or filesystem problems. The scaffold is
    assembled in a temporary sibling directory (copies, manifest, review
    summary, sql/) and only moved into place after every step succeeds, so a
    failure leaves the destination untouched and retryable. Only the empty
    destination directory the caller provided is ever removed (immediately
    before the final rename).
    """
    dest = Path(dest)
    templates_dir = Path(templates_dir)
    if dest.exists():
        if not dest.is_dir():
            raise NotADirectoryError(f"destination exists and is not a directory: {dest}")
        if any(dest.iterdir()):
            raise FileExistsError(f"destination is not empty, refusing to overwrite: {dest}")
    if not templates_dir.is_dir():
        raise FileNotFoundError(f"templates directory not found: {templates_dir}")

    workstreams = dedupe_workstreams(workstreams)
    artifact_paths = resolve_artifact_paths(workstreams)
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=STAGING_PREFIX, dir=dest.parent))
    try:
        created_names = []
        for key in sorted(artifact_paths):
            filename = ARTIFACT_TEMPLATE_FILES[key]
            template = templates_dir / filename
            if not template.is_file():
                raise FileNotFoundError(f"missing template for artifact '{key}': {template}")
            shutil.copyfile(template, staging / filename)
            created_names.append(filename)

        spec_path = staging / ARTIFACT_TEMPLATE_FILES["analysis_spec"]
        spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
        fill_analysis_spec(spec, project_id, title, workstreams, artifact_paths)
        spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        review_path = staging / ARTIFACT_TEMPLATE_FILES["review_summary"]
        review_text = review_path.read_text(encoding="utf-8-sig")
        review_path.write_text(
            fill_review_summary(review_text, project_id, title), encoding="utf-8"
        )

        if "data-mining" in workstreams:
            sql_dir = staging / "sql"
            sql_dir.mkdir()
            readme = sql_dir / "README.md"
            readme.write_text(
                "# Ad hoc SQL for this project\n\n"
                "Keep queries here as reviewed text files. Never store credentials or\n"
                "connection strings in this folder; this skill performs no live queries.\n",
                encoding="utf-8",
            )
            created_names.append("sql/README.md")

        if dest.exists():
            dest.rmdir()  # only reachable when the caller-provided dir is empty
        os.replace(staging, dest)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return [dest / name for name in created_names]


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="init_project.py",
        description="Scaffold a banking data analytics project from skill templates "
        "(offline draft-and-validate; no connections are created).",
    )
    parser.add_argument("dest", type=Path, help="destination project directory")
    parser.add_argument("--project-id", required=True, help="project identifier, e.g. PRJ-0001")
    parser.add_argument("--title", required=True, help="human readable project title")
    parser.add_argument(
        "--workstreams",
        nargs="+",
        required=True,
        choices=list(WORKSTREAMS),
        help="one or more workstreams to enable",
    )
    args = parser.parse_args(argv)
    if not args.project_id.strip() or not args.title.strip():
        parser.error("--project-id and --title must be non-empty")
    try:
        created = build_project(
            args.dest, args.project_id.strip(), args.title.strip(), args.workstreams
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for path in created:
        print(f"created {path}")
    print(f"project scaffolded at {args.dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
