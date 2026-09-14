---
name: review
description: >-
  Run an AST-aware semantic review of local changes, in the style of popular
  code-review tools, against a base ref before they are pushed: map changed
  files into cohorts, reason over a syntax-aware structural diff (never raw
  file dumps), chase changed signatures to their call sites, and report
  findings by cohort with a high/medium/low severity rubric and a
  ship-it/fix-required verdict. When a
  planned shipd change is in scope, verify the diff against its delta scenarios.
  Read-only; a `--json` mode feeds the future PR gate. Use when asked to
  "review my changes", run a "semantic review", review a diff/branch/PR before
  pushing, or "/s:review". Trigger phrases: "review my changes", "semantic
  review", "review this diff", "/s:review".
---

# /s:review — Semantic review engine

You are running a review in the style of popular code-review tools over the
user's **local, unpushed changes** against a base ref — *before* they open a
PR, so problems are caught while they are cheap to fix.

`semdiff` does the mechanical work and emits compact JSON. **You** supply the
judgement. Never read whole files into context when the structural diff and
targeted lookups will do — that is the entire point.

Invoke the engine as (it is a plugin script, not a PATH binary):

```
python3 "$CLAUDE_PLUGIN_ROOT/skills/review/scripts/semdiff.py" <subcommand> ...
```

Subcommands: `diff`, `files`, `context`, `change`, `doctor`. All review
subcommands are read-only and never touch the network; only `doctor --fix`
installs software or reaches the network, and the single place this skill runs
it is the review-start difftastic repair (see Degradation).

## References

Each file below is read only when its condition fires — not by default.

| Reference | Load when |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/spec-aware.md` | the user named a planned change, or exactly one change exists under `planned/` |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/json-output.md` | the user passed `--json`, or the poster's JSON is being produced |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/posting.md` | posting to a PR was explicitly requested |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/risk-lenses.md` | a risk lens trigger fires during review of the diff |

## Determine what to review

- **Local changes before pushing** (the default): `diff <base>` compares
  `<base>` against the working tree. If the user did not name a base, default
  to `main` (fall back to `master`).
- **An already-pushed branch or PR**: when the user names two refs, pass a
  head — `diff <base> <head>`. This reviews what `<head>` added since it
  diverged from `<base>` using PR-style merge-base (three-dot) semantics,
  matching what GitHub shows — the "after" content comes from `<head>`, not
  your checkout. Add `--linear` for a plain two-dot comparison. Refs must
  exist locally (fetch first). The output echoes the resolved
  `base`/`head`/`mode` so you can state precisely what was compared.

## Workflow

Before step 1, run the review-start difftastic check (see Degradation) — it is
the only step that may install anything, and it runs before any analysis.

### 1. Map the change
Run `files <base> [<head>]` to see changed files grouped into architectural
cohorts (contracts, database, api, frontend, tests, plus the shipd `skills`
and `specs` cohorts for this repo's own artifacts). Review **cohort by
cohort**, foundational layers first (contracts and database before api before
frontend) — not alphabetically, not file-by-file.

### 2. Read the structural diff
Run `diff <base> [<head>]`. Per-file, syntax-aware hunks with formatting-only
noise stripped. Reason about *what changed structurally* — new/removed/modified
signatures, altered control flow, changed contracts — from this JSON. Do
**not** open the raw files unless a hunk is genuinely ambiguous. Each file
entry carries an `engine` field (`difft` = syntax-aware; `text` = the
degradation engine); the summary carries `signature_changes`, a best-effort
count you refine.

### 3. Check downstream impact
For any changed function/type/message signature, run `context <symbol>` to find
references. Use `--lang` / `--path` to cut noise on common names.

- Callers that appear in `context` but **not** in the diff are your
  highest-value findings: code the user changed a contract for but did not
  update.
- Treat every match as a **candidate to verify, never as "safe."** The lookup
  is best-effort grep, not a complete call graph. Unmatched files are *not*
  proven unaffected — say so rather than implying coverage you do not have.
- `--lang` filters by extension and misses extensionless scripts — retry
  without it before concluding there are no references.
- **Changed constants are contract changes.** A changed limit, bound, timeout,
  retry count, buffer size, or threshold is not a stylistic tweak — it changes
  what callers can rely on. Chase every consumer of the changed constant
  through `context <symbol>` exactly as you would a changed signature.
- **Uneven sibling sites.** When the diff touches two or more parallel
  implementations of the same thing (sibling handlers, mirrored engines,
  duplicated validation), compare them against each other, not only against
  the base. Name any hardening, guard, or edge-case handling applied to one
  and not the other.

### 4. Trace call-site values — reachability and comment accuracy
Do not judge a new branch, guard, or helper in isolation — follow the actual
argument each call site passes in:

- **Unreachable guard / dead branch.** A defensive branch the real call can
  never hit. Flag it as dead code, and never describe it in the walkthrough as
  if it executes.
- **Comment / intent vs. actual behaviour.** A comment that promises behaviour
  the code does not produce given how it is called is wrong even though the
  line it sits on exists.

Both are usually low severity alone, but they compound. Whenever you quote a
mechanism in the walkthrough, confirm the path that reaches it actually runs
with the values the call sites supply.

### 5. Judge new code on its own terms
For every function, class, guard, or helper the diff introduces, judge it
against its own stated purpose — do not wave it through because it is new
rather than modified:

- **Wrong quantity measured.** A limit, cap, or check that measures the wrong
  thing (bytes where the guarantee is about lines, wall time where it is about
  CPU time) looks correct and is not.
- **Escape hatch lapsing the guarantee.** A flag, default, or fallback branch
  that quietly steps around the very invariant the code exists to enforce.
- **Termination on hostile input.** Does the routine terminate — and cheaply —
  on empty, oversized, malformed, or adversarial input, not only the input the
  happy-path test exercises?
- **Boundary agreement.** Off-by-one and inclusive/exclusive edges: does the
  code's actual boundary match the one its doc comment or name claims?
- **Doc comment versus code.** Where the new code carries a doc comment or
  docstring, confirm it describes what the code actually does, not what it was
  meant to do.

### 5b. Risk lenses
Check every diff, in every cohort, against five fixed triggers, always — never
gated on cohort or file type. Read
`${CLAUDE_PLUGIN_ROOT}/skills/review/references/risk-lenses.md` for the full
guidance and worked examples once one fires:

- **Secret or credential exposure** — a new literal, log line, or error
  message carrying a key, token, password, or personal data. Always rated
  `high`, whatever the reviewer's confidence.
- **Authorization boundary** — a new route, handler, or query reaching data
  without checking the caller's scope, role, or ownership. Always rated
  `high`.
- **Unbounded work** — a loop, recursion, batch, or fan-out whose size is
  driven by user input or external data with no cap.
- **Resource release** — a file handle, socket, lock, connection, or
  transaction not released on every exit path, including the error path.
- **Migration reversibility** — a schema migration or destructive data
  operation with no down-migration, backup, or recovery path.

### 6. Report by cohort
Group findings under cohort headings, most severe first. For each finding: the
**location**, **what** is wrong, **why** it matters, a concrete **fix**, and an
explicit **severity**.

**Severity rubric.**
- **high** — a correctness bug, a contract break with an un-updated consumer,
  or an unmet spec acceptance criterion.
- **medium** — an unhandled edge case, an untouched caller at genuine risk, or
  a likely-wrong behaviour you cannot fully confirm.
- **low** — style, naming, minor redundancy, defensive nits.
- **Exposure floor.** A secret or credential exposure finding, or an
  authorization boundary reached without the caller's scope check, is always
  `high`, whatever the reviewer's confidence.

Any high **or** medium finding blocks (Fix required); low never blocks. When
unsure between two levels, state the doubt rather than inflating.

### 7. Check test coverage per finding
Run this check over **every** finding you write, at **every** severity —
including low. For each one, ask: would an existing test fail if this defect
regressed? When no test would catch it, raise the gap as its own finding in a
`test-coverage` category (see
`${CLAUDE_PLUGIN_ROOT}/skills/review/references/json-output.md` for the shape),
naming the defect it would guard and where the test belongs. This runs
alongside, not instead of, the finding it covers — a real defect and its
missing test are two findings, not one.

## Presentation (human mode — the default)

1. **Effort score (1–5) at the top**, derived from the diff summary counts
   (files, languages, hunks, kinds, `signature_changes`) plus cohorts touched —
   and, in spec-aware mode, task count and unmet-scenario count. 1 = trivial;
   3 = moderate (several files/cohorts or a signature change); 5 = complex.
   State the number with a one-line justification citing the counts.
2. **Findings header — directly below the effort score.** A line
   `## Findings: <marker> <VERDICT>` — `✅ Ship it` when no finding is high or
   medium; `❌ Fix required` otherwise. This is the **same** decision as the
   verdict in
   `${CLAUDE_PLUGIN_ROOT}/skills/review/references/json-output.md` — never let
   the two diverge. In the summary comment
   `review_gate.py post` upserts, the brand line `**☕ shipd** semantic review`
   precedes this header — it is the first visible line of the comment body,
   directly after the hidden `<!-- shipd-semantic-review -->` marker, which
   stays byte-identical. The pre-rename `<!-- am-semantic-review -->` marker is
   still recognized on read, so a PR whose summary predates the rename is
   edited in place rather than given a second summary comment.
3. **Summary table** — one row per finding, most-severe first, columns
   `# | rating | details`; rating is 🔴 high / 🟠 med / 🟡 low (display label
   `med`; the severity value stays `medium`). No findings → print
   `## Findings: ✅ Ship it` and "No findings." and omit the empty table.
4. **Collapsible walkthrough** in `<details><summary>Walkthrough</summary>`.
5. **Diagrams — only when structurally warranted.** Mermaid: sequence for
   API/flow changes, ER for schema/data-model, state for lifecycle logic.
   Emoji-free labels. Dark-mode-safe: any colour must be low-alpha `rgba()`
   (~0.05–0.15), never opaque pastel fills; never hard-code label text colour;
   never rely on colour alone — label bands as text.
6. **Findings by cohort** — reuse the summary table's numbers — then the
   **verdict** and an explicit list of **what you could not verify**.

## Degradation

`semdiff diff` works even without difftastic — it degrades to a structural-text
engine and stamps `engine: "text"`. A degraded review is never a silent one, and
a missing difftastic is repaired before it costs you accuracy.

**At review start, before any analysis**, check whether `difft` is on PATH:

```
command -v difft
```

- **Present** → proceed directly, syntax-aware. Do **not** invoke the installer.
- **Missing** → run the tiered installer **once**, automatically:

  ```
  python3 "$CLAUDE_PLUGIN_ROOT/skills/review/scripts/semdiff.py" doctor --fix
  ```

  then re-probe with `command -v difft`. This is the one place the skill reaches
  the network, and it reaches it solely through `--fix`. Attempt it **at most
  once per review** — never retry, never loop.
  - **Now present** → proceed syntax-aware with no degradation notice and no
    further ceremony; the repair is not a finding.
  - **Still missing** → the install failed. Then, all three of:
    1. **Tell the user prominently**, before the review body — that difftastic
       could not be installed, that this review therefore runs on the
       structural-text engine (`engine: "text"`) with reduced syntax-aware
       accuracy, and how to install it by hand (e.g.
       `brew install difftastic`).
    2. **Record it as a could-not-verify entry** — in the human mode's
       "what you could not verify" list *and* in `--json`'s `could_not_verify`
       array — naming the text-engine degradation.
    3. **Complete the review anyway** on the text engine. A missing difftastic
       never blocks a review.

Whenever you are on the text engine (or any tool is missing), say so, and do
**not** fall back to dumping raw files. `doctor` (without `--fix`) reports what
is available and touches nothing. git is the one hard requirement.

## Documentation standard

Both the rendered report (Presentation, above) and the posted summary comment
(`review_gate.py post`) are bound to the shipd documentation standard at
`${CLAUDE_PLUGIN_ROOT}/skills/document/references/standard.md`. That file is
the one canonical source of its rules — this section restates none of them;
read it directly. Name one reported defect a **finding** throughout, in the
report, the summary comment, and `--json` — never "issue" or "concern".

## Guardrails

- **Emoji at exactly the three sanctioned sites** — the ☕ mark in the
  `**☕ shipd** semantic review` brand line opening the posted summary
  comment's visible body, the ✅/❌ verdict marker in the findings header, and
  the 🔴/🟠/🟡 severity dots in the summary table. Nowhere else: not in prose,
  findings, other tables, or mermaid labels. The `--json` output described in
  `${CLAUDE_PLUGIN_ROOT}/skills/review/references/json-output.md` carries none.
- **Read-only.** The review never edits the repo.
- **shipd naming only** — no other product branding or brand marks.
- Prefer the tool's JSON over re-deriving diffs; that keeps token cost low.
- Whole-file added/deleted entries have `"hunks": []` and a `"lines"` count. An
  added entry's inlined `content` is reviewed with the same rigour as a hunk —
  never passed on its path and line count alone. When `content_truncated` is
  `true`, read the remainder of the file directly before judging it.

## Question rejection recovery

A known Claude Code bug can deliver an AskUserQuestion interaction as a tool
rejection ("The user doesn't want to proceed with this tool use") even when the
user tried to answer. Never treat a rejected or interrupted AskUserQuestion as
a decline, a stop, or an answer. When the user's next message arrives: if it
answers the pending question, fold it in and continue; otherwise re-offer the
same choices as a plain-text numbered list and wait for a typed reply. Only an
explicitly selected or typed stop/decline ends the flow.
