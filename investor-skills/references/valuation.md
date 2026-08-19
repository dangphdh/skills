# Valuation

Two methods, always shown as ranges: **DCF** (intrinsic) and **comps** (relative). Triangulate — when DCF and comps disagree badly, one of them rests on a bad assumption; find it before trusting either. A mixed "football field" summary closes every valuation.

Use a quick calculation sheet (Python or manual) unless the user asks for a full Excel model. If building Excel: formulas, never hardcodes, for every derived cell — the model must flex when an assumption changes; only raw historicals, drivers, and market data are inputs.

## DCF — 10 steps

**1. Data & validation.** Latest price, shares (diluted — check recent buybacks/issuances), net debt (verify net-cash vs net-debt; sign matters), tax rate sanity (VN corporate rate ~20%, US ~21-25%).

**2. Historical analysis (3-5y).** Revenue CAGR and drivers; gross/EBIT/FCF margin progression; D&A and capex as % of revenue; working-capital behavior; ROIC trend. This is where the forecast comes from — no unexplained jumps between history and projections.

**3. Revenue projection (5-10y).** Fade schedule: years 1-2 near recent visibility, years 3-4 toward industry average, year 5+ approaching terminal growth. Three scenarios:

| | Bear | Base | Bull |
|---|---|---|---|
| Y1-2 growth | e.g. 8-10% | 12-14% | 16-18% |
| Fade to terminal | 1% | 2.5% | 3.5% |

**4. Operating costs.** Model opex lines (S&M, R&D, G&A) as % of revenue with operating leverage — % declines as revenue scales. EBIT = gross profit − opex; target EBIT margin by year 5 must be justifiable (scale, mix, pricing), not aspirational.

**5. Unlevered FCF build:**

```
EBIT − taxes (EBIT × rate) = NOPAT
+ D&A (% revenue)
− capex (% revenue; split maintenance ~2-3% vs growth)
− ΔNWC (% of revenue CHANGE; negative ΔNWC = cash source)
= unlevered FCF
```

**6. WACC.** Cost of equity = risk-free (10Y government bond — 10Y US Treasury, or ~3-4% 10Y VN gov bond for VND analysis) + beta × ERP (5-6%; add a country premium of 1-3% for VN). After-tax cost of debt from interest expense / total debt. Weights at market values. Sanity ranges: large stable 7-9%, growth 9-12%, high-risk 12-15%. VN corporates often sit higher.

**7. Discount.** Mid-year convention (discount periods 0.5, 1.5, …) when cash flows arrive through the year.

**8. Terminal value.** Perpetuity growth preferred: TV = FCF(n+1) / (WACC − g), with g never above long-run nominal GDP / the risk-free rate (≤2.5-3%; VN: use USD-equivalent or real terms — don't let 4%+ VND inflation fake a big TV). Cross-check with exit multiple (EV/EBITDA at mature-peer level). TV >75% of EV ⇒ the model is a terminal-value bet; say so.

**9. Equity bridge.** EV + cash − debt (± minority interests, options dilution) = equity value → per share. Compare with price only at the end — anchoring on the current price corrupts assumptions.

**10. Sensitivity.** 5×5 grid, WACC × terminal g (center cell = base case — must reproduce the model's per-share value; if it doesn't, the grid is wrong). One more grid on the swing driver (e.g. year-5 EBIT margin or revenue growth). Report the bear/base/bull per-share values as the fair-value RANGE.

## Comparable companies

**Peer selection** — same business model, growth, margin, and cycle position beat same industry label. 5-8 names; drop peers whose story differs (a 30%-grower in a 8% peer set poisons the median — or use it deliberately to show the growth premium).

**Core metrics** — pick by question:

- "Cheap vs market?" → P/E (trailing + forward), EV/EBITDA, FCF yield, dividend yield
- "Priced for growth?" → PEG, EV/Sales vs growth
- Sector habits: banks P/B + ROE; REITs P/FFO; insurers P/EV; capital-heavy EV/EBITDA or EV/EBIT; SaaS EV/Revenue + rule-of-40
- The "5-10 rule": EV/EBITDA is ~5-10× P/Sales-ish in intuition terms — when a multiple looks wildly out of line with history or peers, first suspect a denominator problem (depressed EBITDA, one-off earnings), not an actual bargain

**Always show**: company vs peer median vs its own 5Y historical range. Cheap vs peers but at its historical ceiling = not cheap.

**Red flags:** multiples computed on peak margins; "cheap" peers with hidden leverage (check net debt/EBITDA column); growth paid for twice (high EV/Sales AND high P/E — the market rarely gives both for free).

## Football field summary

```
                Low    Mid    High
DCF bear        |——●
DCF base           |——●
DCF bull               |——●
Comps (P/E)         |——●
Comps (EV/EBITDA)     |——●
52-wk range       [———|———]
Current price                ▲
```

Then the one-line verdict: where in its own range the price sits, which assumption the call is most sensitive to, and what evidence would move it.
