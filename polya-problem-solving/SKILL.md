---
name: polya-problem-solving
description: Problem-solving framework in the spirit of George Pólya's "How to Solve It". Use when the user needs to solve, analyze, or plan an approach to a mathematics, logic, algorithm, science, or quantitative problem — or is stuck on one; especially when the solution calls for a methodical presentation, explicit assumptions, and self-verification. Also covers guiding a learner with progressive hints instead of revealing the answer.
---

# Problem solving, the Pólya way

Guide the solution through four phases: **understand the problem**, **devise a plan**, **carry out the plan**, and **look back**. The goal is a correct, followable, verifiable line of reasoning — not just an answer.

Apply proportionally: for a simple question, keep the four phases brief; for a hard problem, pause at decision points to state assumptions or request missing data.

## 1. Understand the problem

Before calculating or writing code, establish:

- **What is sought or decided?** State the goal as symbols, conditions, or concrete success criteria.
- **What is given?** List the facts, definitions, constraints, scope, units, and conventions.
- **What is missing or ambiguous?** Separate stated facts from assumptions. Ask for clarification when missing data would materially change the result; if work can proceed, state a reasonable assumption openly.
- **Is the problem well-posed?** Check for impossibility, contradictions, non-unique solutions, or invalid domains.

Restate the problem in your own words — a model, table, diagram, drawing, or notation whenever that makes the relationships clearer.

## 2. Devise a plan

Choose a direction with a reason before diving into details. Look for a connection to a familiar problem, theorem, invariant, data structure, or model.

Suggested strategies — pick only the relevant ones:

- Try small cases, extremes, or concrete examples to spot a pattern.
- Draw a picture, build a table, write equations, or switch to another representation.
- Decompose into subproblems; work forward from the givens toward the goal.
- Work backward from the goal, then check that each step reverses.
- Recognize patterns, symmetry, invariants, monotonicity, parity, or counting principles.
- Replace the problem with a simpler, analogous, or more general version to find an idea.
- For algorithms: pin down input/output, loop or recursion invariants, correctness, complexity, and edge cases.
- For real-world problems: set evaluation criteria, separate causes from symptoms, and compare options on evidence and cost/risk.

State the plan as short steps. When several plans are viable, prefer the simplest one that is still verifiable; briefly compare trade-offs when they matter.

## 3. Carry out the plan

Implement step by step and make the pivotal reasoning explicit:

- Name the definition, formula, rule, or assumption each step uses.
- Keep notation and units consistent; compute each important transformation.
- When a step leads nowhere, return to the planning phase rather than hiding a leap in reasoning.
- For proofs, ensure every statement follows from the previous ones.
- For code, test behavior on small examples and edge cases while developing.

Never fabricate facts, computations, citations, or certainty levels. If a conclusion depends on an assumption or approximation, say so.

## 4. Look back

Check the result independently of the path just used:

- Substitute the result back into the original conditions, or verify with a different method or representation when feasible.
- Check signs, units, plausible magnitudes, domains, and boundary cases.
- Ask whether a solution, condition, exception, or degenerate case was missed.
- Summarize the key idea: why the plan worked and when it can be reused.
- Where appropriate, note how to shorten, generalize, or improve the solution — without obscuring the main one.

## When stuck mid-solution

When a line of attack stops making progress, stop guessing at random: diagnose the symptom, then pick the matching strategy.

- **The loops keep getting more tangled** — shrink the problem: drop constraints or components, find one simplification that removes many details at once; solve the small version, then extend.
- **No familiar approach fits** — look for a similar problem in another domain or model with the same structure, and borrow its approach.
- **A hidden assumption seems to block the way** — invert it: consider its negation, or work backward from the hoped-for result toward the data.
- **Unsure the result holds at the edges** — test extreme and minimal scales, boundary cases, or degenerate values.
- **The same wrong result repeats** — write down what was tried and why it failed, then change strategy deliberately instead of persisting with the same direction.

## Formal mode for mathematics

When the problem demands academically rigorous reasoning (proofs, derivations, statistics):

- Define every concept before using it; for long work, keep a consistent notation table.
- Choose and state the proof style — direct, contradiction, induction, construction, or case analysis — before writing the details.
- Cite lemmas or standard results instead of reproving them, and record which result is used.
- Additionally check: dimensions or units, symmetry, limiting behavior, existence and uniqueness of solutions.
- For statistics: state hypotheses, choose a test that fits the data type, and report confidence intervals and effect sizes — not just p-values.

## Default answer format

Use the following headings when the problem is non-trivial:

```markdown
## Understand the problem
- Goal: …
- Facts and constraints: …
- Assumptions (if any): …

## Plan
1. …
2. …

## Execution
…step-by-step reasoning or computation…

## Check and conclusion
- Verification: …
- Conclusion: …
- Reusable idea: …
```

Do not impose the full template when the user only wants a short answer. In that case, still perform the internal check and briefly explain the decisive step.

## Short example

**Request:** Find the sum 1 + 2 + … + n.

**Understand:** We need a formula in `n`, with `n` a non-negative integer.

**Plan:** Pair the first number with the last: each pair totals `n + 1`.

**Execution:** There are `n/2` pairs when `n` is even; a similar argument covers odd `n`. Hence the sum is `n(n + 1)/2`.

**Check:** For `n = 4`, the formula gives `10`, matching `1 + 2 + 3 + 4`.

## When the user is stuck

Do not rush to reveal a full solution if they want guidance. Offer questions or hints in increasing order:

1. Recall the goal and which facts are useful.
2. Suggest trying a small case or a different representation.
3. Hint at a matching strategy.
4. Provide the full solution only when the user asks, or after the hints prove insufficient.

When the goal is building the learner's own problem-solving ability, use a faded-guidance sequence instead of just giving answers:

1. Fully work a similar example, explaining what each step does and why.
2. Move to a new problem missing only the final step — the learner completes it.
3. Fade more and more steps until the learner solves one entirely.
4. Raise difficulty after they solve several in a row reliably; return to a fully worked example only when they miss the same step repeatedly.

Support while stuck should be minimal and diagnostic: ask at the exact point understanding broke, rather than doing it for them.
