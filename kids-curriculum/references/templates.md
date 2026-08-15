# Templates — Three Artifacts per Unit

Each unit produces three artifacts. Use these templates. Tokens in `{braces}` are filled per unit; `[brackets]` mark optional sections.

## 1. Teacher Lesson Plan

```markdown
# Lesson: {Lesson Title}

**Subject:** {Math / English Language Arts}  ·  **Grade:** {3 / 4 / 5}
**Topic:** {specific topic, e.g., "Multiplying fractions by whole numbers"}
**Time:** ~{45} minutes  ·  **Lesson #:** {N} of {Total}

## Learning Objective
Students will be able to {observable verb + content}, e.g. "multiply a whole number by a unit fraction and represent the product with a model."

## Materials
- {Student workbook page for this lesson}
- {Any manipulatives, e.g., fraction tiles, whiteboard, protractor}
- {Any text or reading passage, for ELA}

## Prior Knowledge
Students should already be able to {prerequisite skill from an earlier grade or lesson}.

## Lesson Arc

### 1. Warm-up / Hook (5 min)
{A 2–3 minute activity that activates prior knowledge or poses a puzzle. Concrete and quick.}

### 2. Model / Teach (10–12 min)
{Step-by-step demonstration. Show the worked example from the workbook aloud. Think aloud. For ELA, read the passage or model the sentence analysis.}

### 3. Guided Practice (8–10 min)
{Students attempt the guided-practice problems from the workbook while teacher circulates and prompts. Stop to check for understanding after the first problem.}

### 4. Independent Practice (10–15 min)
{Students complete the independent-practice set. Teacher circulates, asks one diagnostic question per student.}

### 5. Closure / Exit Ticket (5 min)
{One problem or one short prompt students complete and hand in. Directly assesses the objective.}

## Anticipated Misconception

**The wrong-but-reasonable idea a student may form:** {name it specifically, e.g., "1/4 is bigger than 1/2 because 4 is bigger than 2."}

**Why it's wrong / how to address it:** {one sentence — e.g., "Return to the area model: the denominator counts equal pieces, so more pieces means each one is smaller."}

## Differentiation

All three tiers target the **same grade-level objective** — scaffolds, not easier content. (See `references/pedagogy.md` for the full model.)

- **Support** (students who would fail Core cold): {1–2 concrete scaffolds — a visual model, a worked-example skeleton, a sentence frame, a math tool, fewer problems}. Use a **fade pattern** — start with 2 scaffolds, drop to 1, then 0 across the set so independence grows. If a prerequisite is genuinely missing, add one short bridge step, then return to grade level. The Support worksheet is **never labeled** as easier to the student.
- **Core** (on-level students): the workbook set as written.
- **Extension** (students who finish Core correctly and fast): {a task that requires NEW thinking — a two-step problem, an open-ended "make your own problem," a transfer task}. Passes the test "what new thinking does this require?" Reject "more of the same" or "bigger numbers."

## Anticipated Student Responses

For the first independent-practice problem, note 2–3 anticipated responses, including at least one wrong-but-informative one. This pre-arms the teacher circulating the room.

> **Problem 1:** {problem}
> - Correct: {what a correct response looks like}
> - Strong: {a correct response that shows deeper understanding, e.g., a labeled model}
> - Watch-for: {a specific wrong response and what it reveals, e.g., "writes 1/9 — student inverted the division; re-anchor 'of means ×'"}

## Assessment
- **Formative:** exit ticket result; observation during independent practice
- **Exit ticket (misconception-tested):** {one problem or short prompt. A student holding the day's main misconception must get this WRONG. If they'd still get it right, the ticket is too easy — swap it.}
- **Success criterion:** {e.g., "7 of 8 independent problems correct = proficient"}

## Notes for the Teacher
{Any tricky phrasings, materials tips, or common pitfalls. Keep it to 2–4 bullets.}
```

## 2. Student Workbook Page

The workbook page is what the kid sees. Tone is warm and second-person. One concept only.

```markdown
# {Lesson Title}

**Today you will learn how to** {kid-friendly restatement of the objective}.

---

## 🔍 Worked Example

{Explain the concept in 1–3 short sentences. Then show ONE fully worked example, step by step, in a box:}

> **Example.** {Problem}
>
> **Step 1:** {first step with brief reasoning}
> **Step 2:** {second step}
> **Answer:** {final answer, with the unit or label}
>
> 💡 {One tip or "why it works" note}

---

## 🤝 Let's Try Together (Guided Practice)

{2–3 problems, scaffolded from easy to slightly harder. These are done with teacher support. Leave work space.}

1. {Problem}

   *(show your work below)*

   ____________



2. {Problem}

   *(show your work below)*

   ____________

---

## ✏️ On Your Own (Independent Practice)

{5–8 problems, mixing the same skill. For ELA, mix item types: short answer, multiple choice, find-the-evidence.}

1. {Problem}
2. {Problem}
3. {Problem}
4. {Problem}
5. {Problem}

*(continue on the back if you need more room)*

---

## 🌀 Mixed Review

{2–3 problems pulling from a previous lesson or unit. Keeps earlier skills sharp.}

1. {Review problem}
2. {Review problem}
```

**Visual rules for the workbook page (applied at export):**
- Worked Example lives in a bordered box.
- Each open-response math problem has at least 2 blank lines or a work-space box beneath it.
- Multiple-choice options A/B/C/D each on their own line.
- Bold headers for each section so a kid can find their place.
- One lesson = one printable page where possible (Grades 3–5; a second page is fine for Grade 5).

## 3. Answer Key

```markdown
# Answer Key — Lesson {N}: {Lesson Title}

## Guided Practice
1. **{Answer}** — {one line of method, e.g., "4 × 1/3 = 4/3; 4/3 = 1 1/3"}
2. **{Answer}** — {method}

## Independent Practice
1. **{Answer}** — {method or, for ELA, "Accept {valid response that …}."}
2. **{Answer}** — {method}
... (all problems)

## Mixed Review
1. **{Answer}** — {which earlier lesson this reviews}
2. **{Answer}** — {method}

## Notes
- {Most-missed problem and the likely misconception.}
- {If an ELA item is open-ended, list the criterion: "Full credit = names a character trait AND gives one detail from the text."}

## Verification
**Every answer was re-worked from scratch against the key before this page was shown.** {Confirm: yes / no. If no, stop and fix.} No invented solutions. For math, the operation count of the worked solution matches the standard method.
```

For ELA open-ended items, the answer key gives a **scoring criterion**, not a single correct sentence, because responses vary. Always state what full credit requires.

## Assembling a multi-lesson unit

When a unit has several lessons, decide the document structure with the user, then stay consistent. Two common arrangements:

**A. By lesson (teacher + student together):**
```
Cover / Table of Contents
Lesson 1: [Lesson Plan] [Workbook Page] [Answer Key]
Lesson 2: [Lesson Plan] [Workbook Page] [Answer Key]
...
```

**B. By audience (teacher's guide vs. student book):**
```
Teacher's Guide
  - Lesson 1 plan + answer key
  - Lesson 2 plan + answer key
Student Workbook
  - Lesson 1 page
  - Lesson 2 page
```

**B is usually better for distribution** (you can hand kids only their pages). Default to asking the user which they prefer; if they say "you decide," use B.

## Cover page (for either arrangement)

```markdown
# {Unit Title}
### {Subject} · Grade {3/4/5}

{Optional short description, e.g., "A 6-lesson unit on multiplying and dividing fractions."}

**Contents**
- Lesson 1: {title} ... p. {N}
- Lesson 2: {title} ... p. {N}
...
```

Page footer on every page: `Grade {X} · {Subject} · Page {N}`.
