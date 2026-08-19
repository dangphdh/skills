# Portfolio Management

For a personal portfolio, management is mostly **writing rules when calm and following them when emotional**. The agent's job: keep the target policy, flag drift, and report performance honestly.

## Setup — the Investment Policy (one short markdown file)

If the user doesn't have one, draft it together and store it next to the theses (workspace, e.g. `portfolio/policy.md`):

- **Goal & horizon**: what this money is for, years to need it
- **Target allocation**: % per asset class / sector / single-stock cap (typical guardrails: single position ≤10-20%, one sector ≤25-40%, cash buffer sized to sleeping quality)
- **Rebalancing rule**: band-based — rebalance a position when it drifts ±5 percentage points from target (absolute) or ±25% (relative), whichever hits first; otherwise leave it alone
- **Contribution/withdrawal plan**: monthly amount, where it defaults to
- **Sell discipline**: sell on thesis-break (from stock-research.md tracker), on better-use of capital, or on rule-based rebalance — never solely because price fell

## Ingesting the portfolio

Accept broker exports / screenshots / manual lists (ticker, shares, cost). Normalize into one table: ticker, name, shares, avg cost, current price, market value, weight %, unrealized P/L, currency. VN brokers quote VND; mixed-currency books need an FX line (state the rate used). Save the normalized file — it becomes the baseline for monitoring.

## Monitoring cadence

- **Per quarter** (or per earnings wave): weights vs targets, thesis scorecards for each holding (from stock-research.md), drift table, top concentration risks
- **Per event**: any holding's catalyst or earnings triggers its earnings-update check
- Output format — one page, board-meeting terse:

```
Portfolio [as of date] — total value, period return, vs benchmark
Drift: [TICKER] 14.2% vs 10% target → action: trim 3% on next strength
Thesis flags: FPT pillar 2 behind · VNM catalyst passed, re-rate
Risks: tech weight 38% vs 25% cap; top-3 = 41% of book
Actions taken / proposed: ...
```

Traffic-light the holdings: green = within band & thesis on track; yellow = drift 5-15pp or a pillar behind (flag, don't force); red = >15pp drift or thesis broken (act now).

## Performance measurement

Keep it simple and honest:

- **Total return** = (end + withdrawals − contributions) / start; for multi-year or lumpy flows, money-weighted IRR (XIRR-style: solve the rate that zeroes the cash-flow series — a 20-line Python script or spreadsheet XIRR)
- **Time-weighted return** when the user times contributions; report both when they differ a lot, and say which skill (market vs timing) drove it
- **Always vs a benchmark**: local index (VN30 / VNI for VN books, S&P 500 or ACWI for global); underperformance periods get reported too
- **Attribution, coarse**: how much came from allocation (which sleeves did well) vs the market beta — a portfolio that beats its index only via 2 concentrated names is a different risk than broad wins
- Rolling 1Y / 3Y numbers, max drawdown, and (nice honesty test) the return of the user's best abandoned discipline

## Rebalancing in practice

1. Compare current vs target weights (the drift table).
2. Only positions outside the band act; inside the band, do nothing.
3. Prefer rebalancing with **new contributions** (tax- and cost-free) before selling.
4. VN specifics: T+2 settlement and per-lot (100-share) sizes mean trims round to lots; selling triggers taxable gains where relevant — note the tax impact before proposing sells.
5. Never rebalance in the same breath as a thesis change — separate the mechanical from the judgmental.

## Risk checks to run every review

- Single position and top-3 concentration
- Sector / factor overlap (two "different" tech holdings are one bet)
- Correlation sanity: what does this book do in a −20% equity month? (estimate from betas/history; don't over-engineer)
- FX exposure if multi-currency; cash drag if >10% sitting idle with no plan
- Any position where size grew because it rose, not because it was re-underwritten — re-run its thesis before letting the winner ride
