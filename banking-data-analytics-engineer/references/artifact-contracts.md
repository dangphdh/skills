# Artifact Contracts

These contracts are binding for project artifacts. Start from `assets/templates/`; do not rename or remove required fields or CSV columns. The offline validator checks structure and internal consistency only. It does not establish business correctness, regulatory compliance, or production readiness.

## Shared rules

- JSON `schema_version` is the string `"1.0"`.
- Use UTF-8. Empty unknown free-text values are `""`, not `null`.
- IDs are stable, non-blank, and unique within their artifact. Prefixes such as `EVD-`, `SRC-`, `ENT-`, `REL-`, `MTR-`, `MAP-`, `QR-`, and `CTL-` are recommended examples, not enforced semantics.
- Dates use `YYYY-MM-DD`; timezones use IANA names such as `Asia/Ho_Chi_Minh`.
- A template placeholder (`REPLACE_WITH_...`, `PROJECT_ID`, `PROJECT_TITLE`, `MODEL_ID`, `QUERY_ID`, `RECONCILIATION_ID`, `YYYY-MM-DD`, `<INSTALLED_SKILL_DIR>`) means the artifact is incomplete. The validator detects the concrete project/artifact/date tokens at handoff; `<INSTALLED_SKILL_DIR>` is documentation notation and must be replaced with the installed skill path when a command is run.
- Semicolon-separate multiple IDs in CSV cells.
- Required CSV columns may be supplemented with documented local columns, but required names must remain present.

### Registry ownership

`evidence-ledger.csv`, `source-inventory.csv`, and `glossary.csv` are shared registries: any enabled workstream appends rows to them, and no workstream owns them exclusively. Every other artifact (`model-spec.json`, `query-spec.json`, `metric-catalog.csv`, `source-to-target.csv`, `quality-rules.csv`, `reconciliation-plan.json`) has exactly one owning workstream at any moment; transfer of ownership is recorded in `review-summary.md`.

### Lifecycle states

Artifact and project lifecycle fields use:

- `draft`
- `blocked`
- `ready_for_human_validation`
- `human_validated`

The agent may set only the first three. `human_validated` requires project-level `human_approval.name` and `human_approval.date` entered by a human.

These are separate from:

- Evidence review state: `pending` | `confirmed_by_human` | `superseded`
- Glossary review state: `proposed` | `validated_by_owner` | `divergent_from_seed`
- Evidence claim state: `observed` | `inferred` | `assumed` | `question`

Do not collapse these vocabularies into one generic status.

### SQL dialect state

`dialect_validation` is `DIALECT_UNVALIDATED` or `DIALECT_VALIDATED`. Three honest combinations exist:

1. Dialect blank (`""`) + `DIALECT_UNVALIDATED` — nothing about the platform is known yet.
2. Dialect named but unconfirmed (for example `"postgresql"` from context or a hedge) + `DIALECT_UNVALIDATED` — a plausible platform name is not evidence; keep SQL conservative.
3. Dialect named + `DIALECT_VALIDATED` — allowed only after documented confirmation (vendor doc, config, owner statement) logged as evidence.

Blank is not required while unvalidated; a named-but-unconfirmed dialect with `DIALECT_UNVALIDATED` is the honest middle state. `DIALECT_VALIDATED` without a cited confirmation is never allowed.

Workstream keys are:

- `domain-modeling`
- `product-discovery`
- `data-mining`
- `quality-reconciliation`

## `analysis-spec.json`

Required fields:

- `schema_version`
- `project{id,title}`
- `status`
- `enabled_workstreams[]`
- `business_question`
- `intended_decision`
- `environment`
- `data_classification`
- `time_context{as_of_date,timezone,cutoff}`
- `platform{dialect,dialect_validation}`
- `owners{business,data,reviewer}`
- `human_approval{name,date}`
- `artifacts{evidence_ledger,source_inventory,glossary,model_spec,query_spec,metric_catalog,source_to_target,quality_rules,reconciliation_plan,review_summary}`

An artifact path is its project-relative filename, or `""` when its workstream is disabled. The initializer always creates `analysis-spec.json` and `review-summary.md`.

Before `ready_for_human_validation`, replace all placeholders; provide the business question, intended decision, environment, classification, time context, and owners; and ensure every enabled workstream's artifact is declared.

## `model-spec.json`

Top-level fields:

- `schema_version`
- `model_id`
- `title`
- `status`
- `evidence_ids[]`
- `entities[]`
- `relationships[]`

Each entity contains:

- `entity_id`
- `name`
- `definition`
- `grain` — one precise sentence describing one row/instance
- `business_keys[]` — non-empty
- `temporal_strategy`
- `classification`
- `evidence_ids[]` — non-empty
- `attributes[]`

Each attribute contains at least `name`, `logical_type`, and `definition`. Optional fields such as `nullable`, `classification`, or `evidence_ids[]` may be added when supported by evidence. Keep types platform-neutral unless the platform is confirmed.

Each relationship contains:

- `relationship_id`
- `from_entity` and `to_entity` — declared `entity_id` values
- `cardinality`
- `optionality`
- `definition`
- `evidence_ids[]` — non-empty

## `query-spec.json`

Required top-level fields match the template:

- `schema_version`, `query_id`, `status`, `business_question`
- `evidence_ids[]`
- `verified_sources[]` — each item resolves to a `source_id` or `object_name` in `source-inventory.csv`
- `result_grain`, `population`, `exclusions[]`
- `metrics[]`
- `time_basis{type,timezone,cutoff}`
- `currency_basis{mode,currencies[],conversion_rule}`
- `dialect`, `dialect_validation`
- `expected_row_behavior`, `validation_checks[]`

Each metric contains `metric_id`, `name`, `formula`, `unit`, `currency`, and `evidence_ids[]`. Its `metric_id` resolves to `metric-catalog.csv`. Every query-spec metric is mirrored in `metric-catalog.csv` by `metric_id` with the same `name`, `unit`, and `currency` and a consistent formula. The validator checks ID resolution and reports name/unit/currency drift; reviewers still compare formula intent. Metric `currency` uses the catalog vocabulary: an ISO 4217 code, `account_currency`, or `not_applicable`.

Currency modes. The template leaves `currency_basis.mode` blank (`""`) while evidence is unresolved and the artifact remains `draft` or `blocked`. The validator deliberately reports that blank as a completion issue—even in draft—so it stays visible rather than becoming a silent default. Before `ready_for_human_validation`, exactly one of the following must hold; never select a mode the evidence does not support:

- `single_currency` — exactly one ISO 4217 currency; explain any conversion in `conversion_rule`, or state `none`.
- `multi_currency` — at least two currencies; state whether results remain partitioned or how conversion is performed.
- `not_applicable` — no monetary measure; `currencies` is empty and `conversion_rule` states `not applicable` or remains empty.

## `reconciliation-plan.json`

Required top-level fields match the template:

- `schema_version`, `reconciliation_id`, `status`, `evidence_ids[]`
- `source_population`, `target_population`, `grain`, `matching_keys[]`
- `time_context{business_date,cutoff,timezone,late_arrival_rule}`
- `currency_controls{mode,currencies[],conversion_rule}`
- `tolerances{count_absolute,amount_absolute,amount_percentage}`
- `controls[]`
- `exception_management{owner,workflow,evidence_retention}`
- `human_approval{name,date}`

`currency_controls.mode` follows the same rule as query-spec `currency_basis.mode`: the blank template value records unresolved evidence in a `draft` or `blocked` plan and is intentionally reported by the validator until replaced with `single_currency`, `multi_currency`, or `not_applicable`. It must be resolved before `ready_for_human_validation`. Tolerance values are non-negative decimal strings. The template's zeroes are draft placeholders, not proof that zero tolerance was approved. Populate values only from cited policy or an accountable human decision made before results are inspected. A zero-tolerance plan at `ready_for_human_validation` must be called out for reviewer confirmation.

Each control contains:

- `control_id`
- `type`
- `description`
- `group_by[]`
- `evidence_ids[]` — non-empty

For `multi_currency`, the currency-grouping requirement binds monetary controls (`amount`, `sum`, or `balance`): each groups by a currency field such as `currency_code` (a field name, not a currency value), because mixed-currency amounts cannot be compared as one pool. Non-monetary controls may use other groupings. `conversion_rule` may state that currencies remain separate rather than being converted.

## CSV artifacts

### `evidence-ledger.csv`

Header:

`evidence_id,state,claim,source_locator,confidence,owner,validation_state`

- `state`: evidence claim state.
- `claim`: dated when time-sensitive.
- `source_locator`: checkable pointer such as `SCHEMA.TABLE.COLUMN`, `docs/x.md § Fees`, `src/q.sql:L42`, ticket ID, or dated chat statement.
- `confidence`: `high`, `medium`, or `low`.
- `validation_state`: evidence review state. Only a human changes it to `confirmed_by_human`.

### `source-inventory.csv`

Header:

`source_id,object_name,object_type,definition,grain,candidate_keys,data_classification,evidence_ids,status`

`object_type` is `table`, `view`, `file`, `report`, `document`, or `other`. `candidate_keys` is semicolon-separated. `status` is a lifecycle state.

### `glossary.csv`

Header:

`term_id,term,aliases,definition,avoid_terms,evidence_ids,owner,status`

`aliases` and `avoid_terms` are semicolon-separated. `status` is a glossary review state, not a project lifecycle state.

### `metric-catalog.csv`

Header:

`metric_id,name,definition,numerator,denominator,grain,aggregation_behavior,time_basis,unit,currency,exclusions,owner,evidence_ids,status`

`aggregation_behavior` is `additive`, `semi_additive`, or `non_additive`. `currency` is an ISO 4217 code, `mixed`, `account_currency`, or `not_applicable`. `status` is a lifecycle state.

### `source-to-target.csv`

Header:

`mapping_id,source_object,source_field,target_object,target_field,target_definition,target_logical_type,nullable,transformation_rule,join_rule,filter_rule,default_rule,grain_impact,data_classification,evidence_ids,quality_checks,unresolved_issue,owner,review_state`

- `source_object` resolves to a source `source_id` or `object_name`.
- State every transformation, join, filter, and default explicitly; use `none` or `not applicable` rather than leaving behavior implicit.
- `quality_checks` contains semicolon-separated `rule_id` references.
- `review_state` is a lifecycle state.

### `quality-rules.csv`

Header:

`rule_id,object_name,field_name,quality_dimension,rule_expression,severity,threshold,owner,evidence_ids,status`

- `quality_dimension`: `completeness`, `uniqueness`, `validity`, `consistency`, `timeliness`, or `accuracy`.
- `severity`: `blocker`, `error`, or `warning`.
- `threshold`: a human-owned value; it may remain blank only while the rule is `draft` or `blocked`.
- `status`: lifecycle state.

## `review-summary.md`

Keep these headings exactly:

- `## Purpose`
- `## Workstream notes`
- `## Evidence summary`
- `## Validation status`
- `## Human validation`
- `## Known limitations`

Record the validator command and result under Validation status. The Human validation section records the named reviewer, date, and outcome; its presence does not by itself change the machine-readable project state.

## Cross-artifact integrity

The validator checks that:

- Evidence references resolve to `evidence-ledger.csv`.
- Query and mapping source references resolve to `source-inventory.csv`.
- Query metric IDs resolve to `metric-catalog.csv`.
- Mapping quality-check IDs resolve to `quality-rules.csv`.
- Model relationship endpoints resolve to declared entities.
- Declared artifact paths exist and match enabled workstreams.
- `human_validated` appears only with complete project-level human approval.
