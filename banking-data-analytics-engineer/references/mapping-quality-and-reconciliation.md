# Mapping, Quality, and Reconciliation

Workstream D: source-to-target mappings, data-quality rules, reconciliation plans, and lineage for bank data flows (report marts, finance feeds, GL to sub-ledger, system to system). Thresholds and tolerances are human decisions; you draft the logic and make every threshold an explicit, owned decision point.

## Source-to-target mapping

One row per target column in `source-to-target.csv`:

- `source_object` resolves to a `source_id` or `object_name` in `source-inventory.csv`; `source_field` may identify a literal or derivation (for example, `LITERAL: 'D'` or `DERIVED: see rule`).
- State `transformation_rule`, `join_rule`, `filter_rule`, and `default_rule` explicitly. Use `none` or `not applicable` when no behavior applies; a blank rule hides decisions.
- `nullable` and `default_rule` together describe NULL behavior. Any default must be evidence-backed or tied to an explicit assumption.
- Use `grain_impact` to state `preserves grain`, `aggregates to ...`, or `fan_out_risk`. Where the source grain is finer than the target grain, document the aggregation grain or leave an `unresolved_issue`.
- Every row cites one or more `evidence_ids`; guessed logic is a `question`, not a mapping rule. `quality_checks` contains referenced quality-rule IDs.

## Data-quality rules

`quality-rules.csv`, one row per rule, classified in `quality_dimension`: completeness (not-null, population coverage), uniqueness (business-key uniqueness, no double-posted events), validity (code lists, ranges, formats), consistency (cross-table invariants: balance equals sum of movements; control totals), timeliness (arrival against cutoff per the documented SLA), accuracy (agreement with an authoritative source).

- Write `rule_expression` precisely and dialect-conservatively; if the platform is unconfirmed, express it in plain SQL-standard form and mark it `DIALECT_UNVALIDATED`.
- `severity` (`blocker`, `error`, or `warning`) is a proposal; `threshold` is human-owned. It may stay empty only while the rule is `draft` or `blocked`, with the pending decision listed in `review-summary.md`. Never invent an "industry standard" threshold.
- Prefer rules that assert a business invariant over rules that assert a datatype; the bank cares about misposted interest, not about VARCHAR lengths.

## Reconciliation planning

`reconciliation-plan.json`, per the artifact contract. Draft in this order:

1. **Populations.** `source_population` and `target_population` as precise filters ("all posted cash transactions, business date = 2026-08-31, branch in scope per memo"). Both sides must state the same time context: `time_context{business_date, cutoff, timezone, late_arrival_rule}`. The late-arrival rule is bank policy; if unknown, it is a `blocked`-level question, not a default.
2. **Grain and keys.** `grain` ("one row per account per business date"); `matching_keys[]` — prefer immutable business keys; if a key is non-unique in either side, that is a prerequisite quality rule, referenced as such.
3. **Currency controls.** If both sides are not same-currency by construction, `currency_controls{mode,currencies[],conversion_rule}` requires the bank's documented conversion policy; without it, `blocked` — never a default base currency or rate.
4. **Tolerances.** `tolerances{count_absolute, amount_absolute, amount_percentage}` are non-negative decimal strings and human-owned decisions made before results are inspected. The template zeroes are draft placeholders, not approved values. Record cited policy or the accountable human decision before handoff; never infer that zero is appropriate.
5. **Controls.** Each `controls[]` item has `control_id`, `type`, `description`, `group_by[]`, and `evidence_ids[]`. Consider count match, signed-sum match, balance-carry-forward, aged-breaks, and no-double-count controls as applicable. For multiple currencies, group monetary controls by a currency field. Derive debit/credit polarity from evidence; do not assume it.
6. **Exception management.** `exception_management{owner, workflow, evidence_retention}`: who receives breaks, through which process, and how long the evidence is kept — per bank policy; unknown means a named question.

Lineage: record the field-level flow (source object.column to target object.column with rules) by referencing `source-to-target.csv` rows, and note any upstream whose own lineage is unknown — that is a traceability gap to report, not to hide.

## Before handoff

All three artifacts contract-valid; every threshold/tolerance either human-approved or explicitly listed as pending; late-arrival and currency policies evidenced or `blocked`; `review-summary.md` carries the reconciliation dry-run checklist (which counts and sums the human compares, on which date, against which control report).
