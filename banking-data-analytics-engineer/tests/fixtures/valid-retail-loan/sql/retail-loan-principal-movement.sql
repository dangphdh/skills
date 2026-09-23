-- Synthetic example query for the valid-retail-loan example project.
-- Analysis: monthly net principal movement and principal event count per loan
-- account, in account currency only (no FX conversion; policy question
-- EVD-0005 is open, so results stay partitioned by currency_code).
-- Object names are placeholders; never point this query at a real environment.
-- Grain: one row per loan account per calendar month of event effective date
-- that has at least one in-scope principal event.
-- Expect: 5 rows on the sample extract — LN-2001 2026-01 and 2026-02,
-- LN-2002 2026-02 and 2026-06, LN-2003 2026-04. LN-2001 2026-03 and
-- LN-2002 2026-03 produce no row because their only principal events are
-- removed reversal pairs.

WITH scoped_events AS (
    -- Duplicate-event guard: the extract may repeat a row (QR-001 asserts
    -- uniqueness; the draft does not rely on it). Keep one row per event_id.
    -- An event_id repeated with differing amounts is a data incident and is
    -- reported by the duplicate probe, not silently resolved here.
    SELECT
        event_id,
        loan_account_id,
        event_type,
        effective_date,
        event_amount,
        ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY effective_date) AS rn
    FROM extracts.loan_event_sample
    WHERE effective_date <= TIMESTAMP '2026-06-30 23:59:59'
),
reversed_event_ids AS (
    -- event_id values reversed by an in-scope reversal row. reversal_link_id
    -- is nullable, so the exclusion below uses NOT EXISTS, never NOT IN
    -- (NOT IN with a NULL on either side never matches).
    SELECT DISTINCT reversal_link_id AS reversed_event_id
    FROM scoped_events
    WHERE event_type = 'REVERSAL'
      AND reversal_link_id IS NOT NULL
),
principal_events AS (
    -- In-scope principal events only. Fees (FEE) are excluded by type, and a
    -- reversed original is removed together with its reversal row
    -- (matched-pair removal, "as if never posted" — the chosen reversal
    -- semantics for this analysis, recorded in the query spec). Reversal rows
    -- themselves are excluded by the event_type filter, so a reversal can
    -- never cancel more than its own original. Rows with NULL event_amount
    -- are excluded from sums and reported by the NULL-amount probe (QR-002).
    SELECT
        e.event_id,
        e.loan_account_id,
        e.effective_date,
        e.event_amount
    FROM scoped_events e
    WHERE e.rn = 1
      AND e.event_type IN ('DISBURSEMENT', 'PRINCIPAL_REPAYMENT')
      AND e.event_amount IS NOT NULL
      AND NOT EXISTS (
            SELECT 1
            FROM reversed_event_ids r
            WHERE r.reversed_event_id = e.event_id
      )
),
scoped_accounts AS (
    -- Duplicate-account guard (QR-005 asserts uniqueness; the draft does not
    -- rely on it). Population filter: accounts opened on or before the
    -- as-of date.
    SELECT loan_account_id, currency_code, segment
    FROM (
        SELECT
            loan_account_id,
            currency_code,
            segment,
            ROW_NUMBER() OVER (PARTITION BY loan_account_id ORDER BY opening_date) AS rn
        FROM extracts.loan_account_sample
        WHERE opening_date <= DATE '2026-06-30'
    ) a
    WHERE a.rn = 1
)
SELECT
    sa.loan_account_id,
    sa.currency_code,
    sa.segment,
    CAST(date_trunc('month', pe.effective_date) AS DATE) AS event_month,
    SUM(pe.event_amount) AS net_principal_movement,
    COUNT(*) AS principal_event_count
FROM principal_events pe
JOIN scoped_accounts sa
    ON sa.loan_account_id = pe.loan_account_id
GROUP BY
    sa.loan_account_id,
    sa.currency_code,
    sa.segment,
    CAST(date_trunc('month', pe.effective_date) AS DATE)
ORDER BY
    sa.loan_account_id,
    event_month;

-- Validation (human-executed; this draft is never run by the agent):
--   1. Row count equals the count of distinct (loan_account_id, event_month)
--      pairs.
--   2. Per-currency SUM(net_principal_movement) ties to reconciliation
--      control CTRL-002; results stay partitioned by currency_code.
--   3. Reversal probe: dropped originals equal the number of in-scope
--      REVERSAL rows with resolvable reversal_link_id (QR-004).
--   4. Duplicate probe: zero event_id values with more than one scoped row
--      before the rn = 1 guard (QR-001); the sample extract plants exactly
--      one duplicate row, so exactly one row should be suppressed.
--   5. NULL-amount probe: rows with NULL event_amount counted and listed
--      separately (QR-002); they are excluded from sums, not silently
--      dropped.
-- Dialect note: the platform is named but unconfirmed
-- (DIALECT_UNVALIDATED). date_trunc and the TIMESTAMP/DATE literals are the
-- constructs to confirm for the target platform at validation.
-- If party attributes are ever joined here, select the party version
-- effective at each row's analysis date (as-of join); PARTY is
-- effective-dated and joining without the as-of predicate fans out.
