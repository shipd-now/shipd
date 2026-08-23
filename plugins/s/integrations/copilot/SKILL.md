---
name: code-review
description: >-
  Run a semdiff-grounded semantic review of this pull request: map the changed
  files into cohorts, reason over the bundled engine's syntax-aware structural
  diff instead of raw file dumps, chase changed signatures to their call sites,
  and report findings with a high/medium/low severity rubric and a
  ship-it/fix-required verdict. Use for every code review of this repository.
---

<!-- shipd-copilot v{version} -->

# shipd semantic code review

This repository ships its own review engine. Use it. `semdiff` does the
mechanical work and emits compact JSON; **you** supply the judgement. Never
read whole files into context when the structural diff and targeted lookups
will do — that is the entire point.

Invoke the bundled engine as:

```
python3 .github/skills/code-review/scripts/semdiff.py <subcommand> ...
```

Subcommands used in a review:

- `files <base> [<head>]` — the changed files, grouped into architectural
  cohorts (contracts, database, api, frontend, tests).
- `diff <base> [<head>]` — per-file, syntax-aware hunks with formatting-only
  noise stripped. Each file entry carries an `engine` field and the summary
  carries a best-effort `signature_changes` count.
- `context <symbol>` — a best-effort reference lookup for a changed symbol.
  `--lang` / `--path` cut noise on common names.

Compare the pull request's base against its head — `diff <base> <head>` — which
uses merge-base (three-dot) semantics, matching what GitHub shows.

## Workflow

### 1. Map the change

Run `files`. Review **cohort by cohort**, foundational layers first (contracts
and database before api before frontend) — not alphabetically, not
file-by-file.

### 2. Read the structural diff

Run `diff`. Reason about *what changed structurally* — new/removed/modified
signatures, altered control flow, changed contracts — from that JSON. Do
**not** open the raw files, and never paste raw file dumps into your reasoning,
unless a hunk is genuinely ambiguous.

### 3. Check downstream impact

For any changed function, type, or message signature, run `context <symbol>` to
find its references.

- Callers that appear in `context` but **not** in the diff are the
  highest-value findings: code whose contract changed but which was not
  updated.
- Treat every match as a **candidate to verify, never as "safe."** The lookup
  is best-effort grep, not a complete call graph. Unmatched files are *not*
  proven unaffected — say so rather than implying coverage you do not have.

### 4. Trace call-site values

Do not judge a new branch, guard, or helper in isolation — follow the actual
argument each call site passes in. A defensive branch the real call can never
hit is dead code; a comment promising behaviour the code does not produce given
how it is called is wrong even though its line exists.

### 5. Report

Write a report that is **scanned**, not read start to finish: the verdict
first, then a table that rates every finding, then the detail. A reader who
stops after the first screen must already know whether the pull request ships
and what the worst problem is. Never open with a transcript of your
investigation.

The body's shape, in this order:

1. **The verdict header, as the body's first line** — the header states the
   verdict the rubric below produces:

   ```
   ## Findings: ✅ Ship it
   ```

   ```
   ## Findings: ❌ Fix required
   ```

2. **A severity summary table, before any per-finding detail** — one row per
   finding, numbered, rating it 🔴 high / 🟠 med / 🟡 low, with its location
   and a one-line statement of the defect:

   ```
   | # | rating | details |
   | --- | --- | --- |
   | 1 | 🔴 high | `src/api/handler.py:88` — the retry loop never resets the backoff |
   ```

   No findings: say `No findings.` in place of the table.

3. **The per-finding detail**, grouped by cohort, most severe first, each
   numbered to match its table row. For each finding give the **location**,
   **what** is wrong, **why** it matters, a concrete **fix**, and its
   **severity**.

   Keep each finding brief — a few sentences, the evidence that makes it
   checkable, and nothing else. Detail that a reader must wade through is
   detail that does not get read: no restating the diff, no narrating how you
   found it, no repeating the table.

The 🔴/🟠/🟡 dots of the table and the ✅/❌ of the verdict header are the only
emoji this report carries. Nowhere else: not in prose, in the detail, or in
other tables.

**Also write the findings as data.** Beside the report body, write a
machine-readable findings file at

```
$RUNNER_TEMP/shipd-copilot-review-findings.json
```

(the working directory when `RUNNER_TEMP` is unset, matching the workflow's
`${RUNNER_TEMP:-.}`). It is how the gate workflow anchors your findings onto
the diff as inline comments — you never post anything yourself. Writing it is
best effort: a surface where you cannot write files simply produces the body,
and the gate posts that body with nothing anchored.

The file is a JSON array, one entry per finding, in the same order and
numbering as the summary table:

```json
[
  {
    "severity": "high",
    "path": "src/api/handler.py",
    "start_line": 88,
    "end_line": 92,
    "detail": "The retry loop never resets the backoff, so a recovered call keeps the maximum delay for the rest of the session.",
    "replacement": ["        backoff = INITIAL_BACKOFF", "        attempts = 0"]
  }
]
```

- `severity` is `high`, `medium`, or `low` — the same rubric as the table.
- `path` is repo-relative, exactly as the diff names the file.
- `start_line`/`end_line` are the RIGHT-side (new-file) line range the finding
  is about, `start_line <= end_line`; a single line repeats it in both.
- `detail` is the prose a reader gets on the inline comment — brief, the same
  substance as the report's per-finding detail.
- `replacement` is **optional** and carries the whole replacement lines for the
  range. Include it **only** where you judge the fix confident and expressible
  as one or more contiguous whole lines — its presence is that judgement, and
  it becomes a one-click committable suggestion whose correctness rests on
  whoever clicks. A partial-line edit, a fix spanning separate ranges, or one
  you are unsure of: omit `replacement` and let the detail say it in prose. The
  line count need not match the range; a fix may add or remove lines.
- Valid JSON only, no emoji, no fences around the file's own content.

The workflow verifies every `path` and range against the diff it computes
itself; a finding it cannot place there is folded into the posted body as prose
instead of being anchored. So the file never decides what the review says — the
body remains the review, and the verdict marker below is what gates the merge.

**Severity rubric.**

- **high** — a correctness bug, a contract break with an un-updated consumer,
  or an unmet acceptance criterion.
- **medium** — an unhandled edge case, an untouched caller at genuine risk, or
  a likely-wrong behaviour you cannot fully confirm.
- **low** — style, naming, minor redundancy, defensive nits.

**Verdict rule.** Any high **or** medium finding blocks: the verdict is
**Fix required**. With no high and no medium finding, it is **Ship it**.
Low findings never block. When unsure between two levels, state the doubt
rather than inflating.

**End the review body with the verdict, twice.** A human-readable verdict line
— `**Verdict: Ship it**` or `**Verdict: Fix required**` — and, on its own line
directly below it, the matching machine-readable marker:

```
<!-- shipd-verdict: ship-it -->
```

```
<!-- shipd-verdict: fix-required -->
```

Emit exactly one marker, matching the verdict line, as the last line of the
body. It is read from the body's **last non-empty line**, by exact equality —
never by a substring match elsewhere in the body, because a review that quotes
a marker while describing a diff would otherwise be read as having voted it. So
reproduce it character for character, on its own line, with nothing after it:
no reflowing, no extra spaces inside the comment, no sign-off below it.

## The engine's guarantees and limits

- **Read-only.** Every subcommand above only reads the repository and shells
  out to `git`; none of them writes, and none of them reaches the network. The
  review must not edit the repository either.
- **Degradation is safe.** `difft` (difftastic) makes the diff syntax-aware but
  is never required: when it is unavailable the engine falls back to its
  structural text engine and stamps `engine: "text"` on the affected entries.
  When you see the text engine, say so in the review — and still do **not**
  fall back to dumping raw files. `ripgrep` is likewise optional; `context`
  falls back to `git grep`. The repository's
  `.github/workflows/copilot-code-review.yml` preinstalls both on the runner.

## Scope of this review

- **One contract, both reviewer surfaces.** This file is the review contract
  for each of the two surfaces that consume it: GitHub's own Copilot
  code review runs, and the gate workflow's headless Copilot CLI reviewer,
  whose prompt names this file instead of restating the rubric. Whichever one
  is reading, the workflow, the rubric, and the verdict rule above are the
  review.
- **No repository-side model selection.** The GitHub Copilot code-review
  surface exposes no repository-side option to pin the model this review runs
  on, so nothing here configures one. This is documented rather than faked; it
  will be revisited if GitHub exposes a real option.
- **This review can be the merge gate.** Where the repository installs
  `.github/workflows/copilot-review-gate.yml`, that workflow reads the verdict
  marker above out of the review text — this body, or the report the CLI
  reviewer wrote — and posts it as the `semantic-review` commit status on the
  reviewed head commit: a `fix-required` marker posts
  `failure` and blocks the merge, a `ship-it` marker posts `success`. A review
  body carrying **no** marker follows the repository's `SHIPD_GATE_FAIL_OPEN`
  Actions variable: unset — the default — it is **fail-open**, posting
  `success` with a description saying no verdict was parsed, so a missing
  marker never bricks a merge but throws this review's judgement away; set to
  `false`, nothing is posted at all and the required check stays `pending`
  until a human clears it. Either way the marker is what makes this review
  count. Emit it.
- **Advisory where no gate workflow is installed.** Without that workflow the
  review posts as an ordinary Copilot review and blocks nothing on its own;
  whatever status check the repository requires remains the merge gate. Either
  way, report honestly: the verdict follows the rubric, never the consequence.

---

These files are installed and upgraded by `shipd copilot add`. Edit the
templates in the shipd plugin (`integrations/copilot/`) rather than the
installed copies, which a re-`add` overwrites.
