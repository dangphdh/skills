# Operating Process

Lifecycle for a banking data analytics engagement. Read this and `safety-and-evidence.md` before workstream work. This file defines how the engagement runs; the workstream references define the craft.

## Session start

1. Look for an existing `analysis-spec.json` in the project (normally copied from `assets/templates/analysis-spec.json`). If found, resume: read `status`, `enabled_workstreams`, `owners`, and every artifact it links before doing anything.
2. If none exists, draft one from the template — or scaffold the project first with the initializer, run from the installed skill directory (script paths resolve from the installed skill, never from the project): `python <INSTALLED_SKILL_DIR>/scripts/init_project.py DEST --project-id ID --title TITLE --workstreams <workstream...>`. A fresh scaffold is intentionally incomplete; expect validator findings and let them guide completion. Fill only what the user or evidence supports; park unknowns as `question` entries in `evidence-ledger.csv` (states are defined in `safety-and-evidence.md`).
3. Confirm scope in one batched message: business question, intended decision, environment (where the data/metadata comes from), data classification, platform and dialect (confirmed or not), time context, enabled workstreams, owners. Do not start modeling or SQL before `business_question` and `intended_decision` are recorded.

## Project states

Set exactly one value in `analysis-spec.json` `status` and mirror it in `review-summary.md`:

| State | Meaning | Who sets it |
|---|---|---|
| `draft` | Work in progress; artifacts may be incomplete; open questions allowed | Agent |
| `blocked` | Cannot proceed without a human or bank input; blocker, requested item, and owner recorded in `review-summary.md` | Agent |
| `ready_for_human_validation` | Draft complete per the exit checklist below; awaiting human review | Agent |
| `human_validated` | A named human reviewed and accepted the artifacts on a stated date | Human only |

Hard rules:

- Never set `human_validated`, and never fill `human_approval{name,date}` yourself. If a user says "approved" in chat, ask them to state their name and the date for the record; log their statement as `observed` evidence with the chat date as locator, but the status value itself is entered by the human, not invented by you.
- When `blocked`, state precisely: what is missing, who must supply it, and what you will do the moment it arrives. A well-formed blocker is a good outcome; silent guessing is not.

## Workstream loop

Per unit of work:

1. Route to one workstream (SKILL.md) and read only its reference file.
2. Draft or update the artifacts that workstream owns, starting from `assets/templates/` and matching `references/artifact-contracts.md` exactly — downstream tooling parses these files and will reject drifted fields.
3. Log every non-trivial claim in `evidence-ledger.csv` with a state and source locator before citing it from another artifact. Artifact rows reference evidence by `evidence_ids[]` / `evidence_id`.
4. Close the loop in `review-summary.md`: what changed, what is open, current status, and what the reviewer must check.

## Asking questions

- Batch clarifying questions. Make each answerable and, where possible, multiple-choice with a recommended option and the reason.
- If the user cannot answer now: record the open point as a `question` evidence row, and where it is safe proceed on an explicitly labeled `assumed` row while status stays `draft`. Never convert an unanswered question into an unstated assumption, and never list a question in the ledger while quietly treating it as settled in prose.
- Safety-gated inputs are different — without them you stop, not proceed: small-cell/publication policy, currency conversion policy, data classification, retention rules. Set `blocked` (see `safety-and-evidence.md`).

## Exit checklist for `ready_for_human_validation`

All must hold; otherwise stay `draft` or `blocked`:

- `analysis-spec.json` complete: business question, intended decision, environment, data classification, time context, owners named, `status` current; no enabled workstream is `blocked`.
- Every material claim traces to evidence-ledger entries with checkable locators. Unresolved `question` rows that materially affect results are listed as open items for the reviewer.
- All artifact files match `references/artifact-contracts.md` field contracts and pass the structural validator, run from the installed skill directory (not project-relative): `python <INSTALLED_SKILL_DIR>/scripts/validate_artifacts.py <project_dir>`; record its output under the Validation status section of `review-summary.md`.
- SQL drafts carry truthful `dialect` and `dialect_validation`; `DIALECT_UNVALIDATED` whenever the platform was never confirmed by evidence.
- Safety-gated items (small-cell policy, currency basis, tolerance approvals) are satisfied — or the artifact that depends on them is held and status is `blocked` instead.
- `review-summary.md` contains decisions needed from the reviewer and a concrete validation checklist (queries to run, counts to compare, spot checks) for the human to execute. You never execute these yourself.

## Progressive loading

Load references only when routed: the two shared files once per engagement; the one workstream reference for the task at hand; `artifact-contracts.md` before creating or editing any artifact; `banking-semantic-starter.md` when validating banking terms; `reference-sources-and-licenses.md` when quoting or adapting external material. Never read all reference files reflexively; never paste reference content wholesale into answers.
