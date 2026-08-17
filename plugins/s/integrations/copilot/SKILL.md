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

Group findings by cohort, most severe first. For each finding give the
**location**, **what** is wrong, **why** it matters, a concrete **fix**, and an
explicit **severity**.

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
body. It is read by an exact substring match, so reproduce it character for
character — no reflowing, no extra spaces inside the comment.

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

- **No repository-side model selection.** The GitHub Copilot code-review
  surface exposes no repository-side option to pin the model this review runs
  on, so nothing here configures one. This is documented rather than faked; it
  will be revisited if GitHub exposes a real option.
- **This review can be the merge gate.** Where the repository installs
  `.github/workflows/copilot-review-gate.yml`, that workflow reads the verdict
  marker above out of this review's body and posts it as the `semantic-review`
  commit status on the reviewed head commit: a `fix-required` marker posts
  `failure` and blocks the merge, a `ship-it` marker posts `success`. The
  bridging is **fail-open** — a review body carrying no marker posts `success`
  with a description saying no verdict was parsed — so a missing marker never
  bricks a merge, but it also throws away this review's judgement. Emit the
  marker.
- **Advisory where no gate workflow is installed.** Without that workflow the
  review posts as an ordinary Copilot review and blocks nothing on its own;
  whatever status check the repository requires remains the merge gate. Either
  way, report honestly: the verdict follows the rubric, never the consequence.

---

These files are installed and upgraded by `shipd copilot add`. Edit the
templates in the shipd plugin (`integrations/copilot/`) rather than the
installed copies, which a re-`add` overwrites.
