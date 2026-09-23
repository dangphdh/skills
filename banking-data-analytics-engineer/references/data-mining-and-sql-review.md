# Data Mining and SQL Review

Workstream C: turn a business question into a draft analytical query, or review an existing query. You draft; the human runs, on their environment, with their credentials, which you never see. Every query draft is recorded with its `query-spec.json` entry.

## Spec before SQL

Never jump to SQL. Fill `query-spec.json` first:

- `business_question` copied/derived from `analysis-spec.json`.
- `verified_sources[]`: only sources present in `source-inventory.csv` with confirmed object names. A table name you cannot verify in evidence does not enter a draft.
- `result_grain`: one sentence — "one row per account per business date".
- `population` and `exclusions[]`: who/what is in and out ("facilities with a disbursed amount > 0"; exclude "internal test branches, per ETL spec §4").
- `metrics[]`: each with `metric_id`, `name`, a plain-language `formula`, `unit`, `currency`, and `evidence_ids[]`. Describe numerator and denominator explicitly for ratios.
- `time_basis`, `currency_basis`, `expected_row_behavior`, `validation_checks[]` per the artifact contract.

If any of these cannot be filled from evidence, that is the finding: record the `question`, and either stop at the spec or proceed with flagged `assumed` values while status stays `draft`.

## Drafting rules

- Build in named CTE stages: source filter, deduplication, joins, measures. Comment each stage with the row count the human should expect (`-- expect: 1 row per account, ~42k rows at 2026-08-31`).
- No `SELECT *`. Name columns; every column's semantics is evidence-backed or flagged.
- Explicit join conditions only; no comma joins, no implicit cross joins.
- `WHERE` clauses on the pre-aggregation stage; state whether filters apply before or after aggregation, because the answer differs.
- Deduplication: when evidence cannot rule out duplicates at the working grain, dedup explicitly (e.g., row-number over the documented business key) and record the chosen rule as an assumption.
- Mark every draft with `dialect` and `dialect_validation`. Unconfirmed platform means `DIALECT_UNVALIDATED` and conservative SQL (standard constructs, no vendor sugar).

## The five recurring traps

**Fan-out.** Joins that multiply rows (customer-to-transactions, account-to-balances-history) silently inflate sums and counts. Detect: state the grain before and after each join; anything not 1:1 or N:1-at-the-grain needs aggregation before joining or a dedup stage. Record expected row behavior and add a pre/post row-count pair to `validation_checks[]`.

**NULLs.** Three-valued logic: `col <> 'X'` drops NULLs; `NOT IN` with a NULL never matches; `SUM` skips NULLs while `COUNT(*)` does not. Decide per column whether NULL means unknown, not-applicable, or a de-facto default — from evidence, not habit. `COALESCE` only with an evidence-backed default, otherwise surface NULLs explicitly. Document the chosen treatment per metric.

**Dates and time.** Banking has posting date, value date, and often a business/date-key. The choice changes results: ask which governs the metric, record it in `time_basis{type,timezone,cutoff}`, and never assume. Normalize timezones explicitly when sources differ; handle late-arriving and back-dated records per the documented rule or flag the rule as unknown.

**Mixed currencies.** Never sum an amount column across currency codes. `currency_basis{mode,currencies[],conversion_rule}` is required: use `single_currency` for exactly one currency, `multi_currency` for two or more currencies (either keep results partitioned and say so, or cite the bank's documented conversion policy), and `not_applicable` for non-monetary results. Without a documented policy, do not convert or default to a base currency or rate—keep results separated by currency or set the conversion-dependent output `blocked`. No hardcoded rates in drafts.

**Effective-dated joins.** Entities whose grain includes an effective period (party, customer, segment, or hierarchy versions — "one row per party per effective period") have many true rows per business key. Joining them to events without an as-of predicate fans out and blends versions: a customer counts once per version instead of once per period. Join on the business key plus the version effective at each row's analysis date (`effective_from <= as_of AND (effective_to IS NULL OR effective_to >= as_of)`), state which date governs the as-of (event date, month-end), and decide explicitly whether you need point-in-time correctness (what was known then) or the current version — they are different queries with different answers. Record the as-of rule in `time_basis` and the result grain, and add a pre/post row-count check on the join.

## Reviewing an existing query

Check, in order: grain matches the stated question; join safety (fan-out, including effective-dated dimensions joined without an as-of predicate); NULL handling; date basis and cutoff; currency handling; exclusions match the population definition; dialect-specific constructs actually valid for the platform; row-count expectations stated. Every defect becomes a specific finding with a locator (line number) and a proposed fix — not "this query has issues".

## Validation plan (human-executed)

Fill `validation_checks[]` with checks the reviewer runs on their environment: row counts at stated dates, sum spot-checks against a trusted report, duplicate-key probes, NULL-rate probes, known-answer tests (one account traced end-to-end). You never execute these; you interpret reported outputs as `observed` evidence.

## Before handoff

`query-spec.json` complete and contract-valid; SQL drafts carry truthful dialect markers; every query-spec metric is mirrored in `metric-catalog.csv` by `metric_id`; small-cell and currency policies resolved or `blocked`; reviewer checklist written in `review-summary.md`.
