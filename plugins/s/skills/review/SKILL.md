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

### 5. Report by cohort
Group findings under cohort headings, most severe first. For each finding: the
**location**, **what** is wrong, **why** it matters, a concrete **fix**, and an
explicit **severity**.

**Severity rubric.**
- **high** — a correctness bug, a contract break with an un-updated consumer,
  or an unmet spec acceptance criterion.
- **medium** — an unhandled edge case, an untouched caller at genuine risk, or
  a likely-wrong behaviour you cannot fully confirm.
- **low** — style, naming, minor redundancy, defensive nits.

Any high **or** medium finding blocks (Fix required); low never blocks. When
unsure between two levels, state the doubt rather than inflating.

## Spec-aware review (when a shipd change is in scope)

Trigger when the user names a change **or** exactly one change exists under
`planned/`. Run `change <name>` — it returns the change's status, deltas
(requirements + WHEN/THEN scenario texts), tasks (checkbox states + progress),
lint findings, and best-effort impact files. Then, against the structural diff:

- **Verify each scenario.** Classify each **Met** (cite the satisfying
  file/hunk), **Unmet** (behaviour absent), or **Can't-tell** (a first-class
  outcome — do not force it). Report every **Unmet** scenario as a
  **high-severity** spec-coverage finding; unmet requirements are the top
  finding and force a Fix-required verdict.
- **Task honesty.** Cross-check `- [x]` tasks against the diff; flag any marked
  done with no supporting change in the diff.
- **Uncovered code.** Behavioural changes no requirement or task describes are
  **observations**, not blockers.
- **Lint findings.** Surface the change's lint findings verbatim.

Report under a **Spec coverage** heading: a Met/Unmet/Can't-tell scenario
table, then the task-honesty and uncovered-code items.

## Presentation (human mode — the default)

1. **Effort score (1–5) at the top**, derived from the diff summary counts
   (files, languages, hunks, kinds, `signature_changes`) plus cohorts touched —
   and, in spec-aware mode, task count and unmet-scenario count. 1 = trivial;
   3 = moderate (several files/cohorts or a signature change); 5 = complex.
   State the number with a one-line justification citing the counts.
2. **Findings header — directly below the effort score.** A line
   `## Findings: <marker> <VERDICT>` — `✅ Ship it` when no finding is high or
   medium; `❌ Fix required` otherwise. This is the **same** decision as the
   `--json` verdict — never let the two diverge. In the summary comment
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

## Machine output mode (`--json`)

When the user passes `--json`, emit a single JSON object to stdout and nothing
else — no preamble, no walkthrough, no diagrams. All analysis still runs; only
rendering changes. Shape:

```json
{
  "verdict": "pass" | "changes-requested",
  "effort": 3,
  "findings": [
    {
      "id": "f1",
      "severity": "high" | "medium" | "low",
      "cohort": "bug" | "contract" | "edge-case" | "untouched-caller" | "spec-coverage",
      "location": "path/to/file.ext:LINE",
      "what": "one-line statement of the defect",
      "why": "why it matters",
      "fix": "concrete fix",
      "status": "open",
      "note": "",
      "suggestion": {
        "confident": true,
        "start_line": 42,
        "end_line": 44,
        "lines": ["the whole replacement line", "and the next one"]
      }
    }
  ],
  "spec_coverage": [ { "scenario": "WHEN … THEN …", "state": "met" | "unmet" | "cant-tell" } ],
  "could_not_verify": [ "…" ]
}
```

Rules: `verdict` is `changes-requested` iff any finding is high or medium, else
`pass`. An unmet acceptance criterion MUST also appear as a `spec-coverage`
finding with severity `high`. `spec_coverage` is present only when a change is
in scope. Valid JSON only — no fences, no commentary, **no emoji**. If the
analysis cannot run, still emit a well-formed object with `could_not_verify`
explaining why.

### The optional `suggestion` object

`suggestion` is **optional** and belongs on a finding only when you would stake
the fix on being applied unread: clicking Apply on a GitHub suggestion commits
your lines verbatim, so the correctness judgement moves to whoever clicks.
Omit it and the finding renders as prose, which is the right answer whenever
you are less than sure.

The poster commits it as a `suggestion` block only when **all** of these hold —
anything else quietly degrades to prose, never an error, so a shape you got
wrong costs a suggestion and not the review:

- `confident` is exactly `true`;
- `start_line` and `end_line` are integers with `start_line <= end_line` — one
  contiguous range, the only shape GitHub can commit;
- `lines` is a non-empty list of the **whole** replacement lines. Its length
  need not match the range: a fix may add or remove lines. Never express an
  edit inside a line — no `start_column`/`end_column`, whose mere presence
  declares a partial-line edit and degrades the finding;
- the finding's `location` anchors to a RIGHT-side line of the PR diff (the
  same rule that decides inline-vs-summary for every finding), and every line
  in `start_line..end_line` is in that diff too — a comment spanning a line the
  diff does not carry is rejected outright.

The range is what the suggestion replaces, and it need not be the `location`
line; the comment anchors on the range. The block changes nothing else about
the finding — same severity marker, same what/why/fix prose — and `--json`
stays emoji- and prose-free.

## Posting to a PR (the gate)

The review verdict gates a PR only once it reaches GitHub. Posting is a
**mechanical** step handled by a companion script — you supply the judgement
(the `--json` object), it shapes the GitHub payloads:

```
python3 "$CLAUDE_PLUGIN_ROOT/skills/review/scripts/review_gate.py" post <pr> --from <json|->
```

**Post only on an explicit request** — the user asking to "post the review to
the PR", or a driving session (the autopilot's `review` stage) instructing you
to. Never post as a side effect of a plain review; a review with no posting
request stays local and touches no `gh` write.

### Review stage options

The invoker — a driving session or the user — may pass two options with the
posting request. Both default to today's behaviour, so a plain "post the
review" changes nothing:

- `disposition=<all|high-only|none>` (default `all`) — how much per-finding
  judgement this review is worth. It selects the posting flow's step 5 (see
  below) and passes straight through to the poster as `--disposition`, which
  maps the `semantic-review` commit status by scope: `all` → `success` iff the
  verdict is `pass`; `high-only` → `success` iff no finding is high; `none` →
  always `success`. The findings and the rendered verdict stay
  severity-honest in every scope — only the merge-gating status is
  policy-aware, and a non-`all` scope is stamped on the summary comment and in
  the status description so a green status over visible findings is explained
  on the PR.
- `model=<tier>` — the model tier this review was meant to run on, symbolic
  (`session`, `tier-below`, `tier-two-below`) or a concrete id. Pass it
  through to the poster as `--model`; it is recorded verbatim as a `Model:`
  line in the summary. **Applying** the tier is the concern of the driver that
  spawns the reviewing session (the autopilot's `review` stage); this skill
  never spawns itself on another model, and interactively the tier is
  informational provenance only.

Never resolve the pipeline configuration yourself — this skill reads no
`autonomous-pipeline` key and infers no options. Whatever the invoker did not
pass, take as the default.

When posting is requested:

1. **Resolve the PR.** `gh pr view <branch> --json number,headRefOid,url` (or
   pass the PR number/URL directly). The branch is usually the current
   `change/<name>`.
2. **Review head vs base with merge-base semantics.** Run the review as
   `diff <base> <head>` (default base `main`) so the "after" side is the PR's
   head exactly as GitHub shows it — the same three-dot semantics described
   under "Determine what to review". Do the full analysis; do not shortcut it.
3. **Emit the machine JSON to a temp file.** Produce the `--json` object (same
   shape and rules as Machine output mode) and write it to a temp path, e.g.
   `"$TMPDIR/review.json"`.
4. **Run the poster.** `review_gate.py post <pr> --from "$TMPDIR/review.json"`,
   adding `--disposition <scope>` and `--model <tier>` when the invoker passed
   them. It upserts the marker summary comment, posts anchored inline comments
   for in-diff findings (folding the rest into the summary), and sets the
   `semantic-review` commit status on the head SHA by scope — under the default
   `all`, `success` iff the verdict is `pass`, else `failure`.
5. **Disposition the findings — by scope.** A posted finding is advice nobody
   is required to read until it is dispositioned, and every gate thread must
   end up carrying disposition evidence. How much judgement you spend depends
   on the acting scope:
   - **`all` (the default) — every finding, low included.** Walk the findings
     (newest post first) and give each exactly one of two dispositions — never
     leave a finding with neither. A finding that is neither implemented (by
     your edit or by its suggestion having been applied) nor replied to is
     undispositioned, and `resolve` will refuse it:
     - **Implement** it when the suggestion is correct: make the edit, commit,
       and push. The push re-triggers the gate, so re-run the review + poster
       afterwards so the summary and status track the new head SHA.

       A finding whose committable `suggestion` block has already been
       **applied** on the pull request is implemented by that very act — the
       commit GitHub made is the evidence — so it needs no edit and **no
       separate reply**. Do not reply "applied" onto such a thread; `resolve`
       reads the later commit as the disposition, exactly as it does for a fix
       you pushed yourself.
     - **Push back** when you judge it not worth implementing: post a concrete,
       reasoned reply onto the finding's thread with

       ```
       review_gate.py reply <pr> <comment-id> --body "<the reason>"
       ```

       where `<comment-id>` is the inline review comment rooting that finding's
       thread. A bare "won't fix" is not a disposition — name the reason.
   - **`high-only` — judgement on the highs only.** Implement each **high**
     finding (or push back on it with a reasoned `reply`, exactly as under
     `all`), re-reviewing and re-posting after any push. Then cover the rest
     mechanically:

     ```
     review_gate.py autoreply <pr> --disposition high-only
     ```

     It posts the canonical policy reply onto every unreplied gate thread
     rooted at a medium or low finding, prints `replied=<n>`, and leaves the
     highs — and any thread whose severity it cannot parse — untouched, so a
     reported unparsed thread still needs your disposition.
   - **`none` — no per-finding judgement at all.** Do not implement and do not
     author individual replies; run

     ```
     review_gate.py autoreply <pr> --disposition none
     ```

     which replies to every unreplied gate thread regardless of severity. The
     findings stay posted and honest; they are simply recorded rather than
     acted on.

   `autoreply` skips threads that already carry a reply, so re-running it after
   a push is safe.
6. **Resolve the threads.** Once every finding is implemented, answered, or
   auto-replied, run

   ```
   review_gate.py resolve <pr>
   ```

   It resolves only the gate-authored threads that carry disposition evidence
   (a reply, or a commit landed after the thread was created), refuses any that
   carry neither (listing them as undispositioned and exiting non-zero), and
   never touches human-authored threads — humans resolve their own. Use
   `resolve <pr> --check` to read the unresolved count without mutating.
7. **Report back** the posted status state (`success`/`failure`), the summary
   comment URL, the acting disposition scope when it is not `all`, and the
   `unresolved=` count from `resolve` — which is **zero** on a completed
   disposition. Any non-zero count means a finding still has no disposition; go
   back to step 5.

The poster is idempotent: re-running after a new push edits the same summary
comment in place and re-stamps the status on the new head SHA. It performs no
analysis of its own — all judgement stays in this skill; the engine only
enforces that each finding was implemented or answered before its thread
resolves.

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

## Guardrails

- **Emoji at exactly the three sanctioned sites** — the ☕ mark in the
  `**☕ shipd** semantic review` brand line opening the posted summary
  comment's visible body, the ✅/❌ verdict marker in the findings header, and
  the 🔴/🟠/🟡 severity dots in the summary table. Nowhere else: not in prose,
  findings, other tables, or mermaid labels. `--json` output carries none.
- **Read-only.** The review never edits the repo.
- **shipd naming only** — no other product branding or brand marks.
- Prefer the tool's JSON over re-deriving diffs; that keeps token cost low.
- Whole-file added/deleted entries have `"hunks": []` and a `"lines"` count;
  when a new file matters, read it directly to review it.

## Question rejection recovery

A known Claude Code bug can deliver an AskUserQuestion interaction as a tool
rejection ("The user doesn't want to proceed with this tool use") even when the
user tried to answer. Never treat a rejected or interrupted AskUserQuestion as
a decline, a stop, or an answer. When the user's next message arrives: if it
answers the pending question, fold it in and continue; otherwise re-offer the
same choices as a plain-text numbered list and wait for a typed reply. Only an
explicitly selected or typed stop/decline ends the flow.
