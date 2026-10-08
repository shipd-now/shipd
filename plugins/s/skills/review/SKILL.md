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
judgement. The structural diff and targeted lookups come first: read a file
only when `related` names it for a check that needs cross-file context — a
file it did not name stays unread, whatever your own judgement makes of it.
Never a raw file dump or model-chosen exploration — that is still the point;
what widens is the engine's own bounded, named set.

Invoke the engine as (it is a plugin script, not a PATH binary):

```
python3 "$CLAUDE_PLUGIN_ROOT/skills/review/scripts/semdiff.py" <subcommand> ...
```

Subcommands: `diff`, `files`, `lint`, `context`, `related`, `change`, `doctor`. All review
subcommands are read-only and never touch the network; only `doctor --fix`
installs software or reaches the network, and the single place this skill runs
it is the review-start difftastic repair (see Degradation).

## References

Each file below is read only when its condition fires — not by default.

| Reference | Load when |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/spec-aware.md` | the user named a change, exactly one change exists under `planned/`, or the diff carries a change directory under `planned/` or `completed/` |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/json-output.md` | the user passed `--json`, or the poster's JSON is being produced |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/posting.md` | a pull request is in scope for the review — it also reads prior findings back before reporting |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/risk-lenses.md` | a risk lens trigger fires during review of the diff |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/linters.md` | `semdiff lint` has run, to interpret each linter's state, weigh its findings, or read the `lint` configuration key |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/new-code-checks.md` | a function, class, guard, or helper is new in the diff |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/pr-description.md` | a pull request's title and description are available |
| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/call-site-tracing.md` | a changed signature, constant, guard, or helper needs chasing to its call sites |

## Determine what to review

**Base freshness — before the first `semdiff` call, every mode.** Fetch the
base's remote:

```
git fetch origin <base>
```

Name the base's own remote where it tracks another one — read it from
`git config branch.<base>.remote` rather than assuming `origin`.

The fetch writes remote-tracking refs only — never the working tree, index, or a local
branch — so the skill's no-modification guarantee holds; it never pulls, rebases, or
checks anything out. The engine resolves a short branch to its remote-tracking commit
once fetched, with no manual staleness check needed. A failed fetch continues the review
with a could-not-verify entry naming the unchecked base, rather than ending it; a
two-ref `lint` run similarly notes that the linters read the checkout, not the reviewed
head, since `lint` passes changed paths to linter binaries that read them from disk.

- **Local changes before pushing** (the default): `diff <base>` compares
  `<base>` against the working tree, defaulting to `main` (or `master`).
- **An already-pushed branch or PR, given as two refs**: `diff <base> <head>`
  reviews what `<head>` added since diverging from `<base>`, PR-style
  (three-dot) — the "after" content is `<head>`, not your checkout. Add
  `--linear` for two-dot (refs must exist locally, see Base freshness,
  above); output echoes the resolved `base`/`head`/`mode`.
- **A named pull request** — a URL, `#<number>`, a bare number, or a branch
  pointed at one: posts its verdict by default, no ask required. See
  `${CLAUDE_PLUGIN_ROOT}/skills/review/references/posting.md` for the flow.

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
Run `diff <base> [<head>]` for per-file, syntax-aware hunks with
formatting-only noise stripped. Reason about *what changed structurally* —
new/removed/modified signatures, altered control flow, changed contracts —
from this JSON. Do **not** open the raw files unless a hunk is genuinely
ambiguous. Each file entry carries an `engine` field (`difft` = syntax-aware;
`text` = the degradation engine); the summary carries `signature_changes`, a
best-effort count you refine.

### 3. Pull related file context
Run `related <base> [<head>]` (default `--mode balanced`: 8 related files per
changed file, 40 across the review; `--mode max` raises both to 20 and 120)
to get each changed file's importers and importees — ripgrep/`git
grep`-backed, best-effort, never a complete call graph, with every truncation
reported as a count rather than applied silently. Read a file this names when
a check below needs context the diff alone does not carry: the
downstream-impact and call-site checks (steps 4 and 5), and the lenses that
compare a change against unchanged code (sibling-consistency in step 4, and
the new-code checks in step 6). A file `related` did not name stays unread —
the engine's named set is what widens this skill's context economy, never
your own judgement about what else might be interesting.

### 4. Check downstream impact
For any changed function/type/message signature, run `context <symbol>` to find
references. Use `--lang` / `--path` to cut noise on common names. Read
`${CLAUDE_PLUGIN_ROOT}/skills/review/references/call-site-tracing.md` for guidance:
- **Untouched callers** — a caller `context` finds that the diff never updated.
- **Every match is a candidate** — grep is not a call graph; name what you could not check.
- **`--lang` misses extensionless scripts** — retry without it before concluding.
- **Changed constants are contract changes** — chase every consumer of the constant.
- **Uneven sibling sites** — compare parallel implementations against each other.

### 4b. Read the linter output
Run `lint <base> [<head>]` over the same endpoints as the diff. Read
`${CLAUDE_PLUGIN_ROOT}/skills/review/references/linters.md` to interpret each
linter's state and findings. A linter finding is corroboration you weigh,
reported only where it bears on the change — never promoted to a review
finding automatically.

### 5. Trace call-site values — reachability and comment accuracy
Do not judge a new branch, guard, or helper in isolation — follow the actual
argument each call site passes in (same reference as step 4):
- **Unreachable guard / dead branch** — a defensive branch the real call never hits.
- **Comment / intent vs. actual behaviour** — a comment the real call sites contradict.

Either alone often looks small, but together they compound. Send both to step
7's rubric to rate by what they do — this step never rates on its own. Whenever
you quote a mechanism in the walkthrough, confirm the path that reaches it
actually runs with the values the call sites supply.

### 6. Judge new code on its own terms
Judge every new function, class, guard, or helper in the diff against its stated
purpose — never wave it through. Read
`${CLAUDE_PLUGIN_ROOT}/skills/review/references/new-code-checks.md` for guidance:
- **Wrong quantity measured** — limit measures the wrong dimension.
- **Escape hatch lapsing the guarantee** — flag or fallback steps around the invariant.
- **Termination on hostile input** — routine terminates cheaply on hostile input.
- **Boundary agreement** — documented boundary matches the actual code.
- **Doc comment versus code** — documented behavior matches the actual code.

### 6b. Risk lenses
Check every diff, in every cohort, against six fixed triggers, always — never
gated on cohort or file type. Read
`${CLAUDE_PLUGIN_ROOT}/skills/review/references/risk-lenses.md` for the full
guidance and worked examples once one fires:

- **Secret or credential exposure** — a new literal, log line, or error message carrying
  a key, token, password, or personal data. Always rated `high`, whatever the reviewer's
  confidence.
- **Authorization boundary** — a new route, handler, or query reaching data without
  checking the caller's scope, role, or ownership. Always rated `high`.
- **Unbounded work** — a loop, recursion, batch, or fan-out whose size is driven by user
  input or external data with no cap.
- **Resource release** — a file handle, socket, lock, connection, or transaction not
  released on every exit path, including the error path.
- **Migration reversibility** — a schema migration or destructive data operation with no
  down-migration, backup, or recovery path.
- **Packaging and dependency manifests** — a manifest or lockfile that disagrees with the
  code, with each other, or omits a new file from what it publishes.

### 6c. Breadth sweep
Revisit each changed file end to end for a remaining defect the structural
diff and signature-chasing steps above do not catch on their own: a swallowed
or silently-dropped error, a resource or file leak on a rare or cleanup path,
dead or duplicated code, a field or variable declared but never read, an
unstable or incorrect identity such as a list key derived from an array
index, or a blocking call in an async context. Send what the sweep finds back
to step 7's rubric to rate — this step never rates on its own.

### 6d. Check the PR description against the diff
When a pull request's title and description are available, read
`${CLAUDE_PLUGIN_ROOT}/skills/review/references/pr-description.md` and check
them against the diff in both directions — every claim against the diff, and
the diff's substantial content against what the description never mentions.
An unmentioned feature has no claim to check, so only the second direction
finds it.

### 7. Report by cohort
Group findings under cohort headings, most severe first. For each finding: a
**location** (the fix site — the line your own fix would change, never a
symptom site in place of it), **what**, **why**, **fix**, and **severity**. A
further location names a site where the defect is visible: a line wrong in
the same way, a line that shows the mismatch on its own terms, or — where the
defect is the conjunction of two lines neither wrong alone — the line at
which it surfaces at run time even though that line is correct in isolation.
When a defect recurs at multiple sites, write one
finding whose `locations` array names every site.

**Severity rubric.**
- **high** — a correctness bug, a contract break with an un-updated consumer, or an
  unmet spec acceptance criterion.
- **medium** — an unhandled edge case, an untouched caller at genuine risk, or a likely-
  wrong behaviour you cannot fully confirm.
- **low** — a real defect whose impact is contained: nothing lost, corrupted,
  exposed, or promised and unmet. Pure style, naming, and formatting are never
  findings.
- **Impact rule.** Rate every finding by what the defect does, not by the kind
  of defect it is: data loss, data corruption, a security exposure, or a
  broken guarantee is `medium` or `high` however minor the kind looks. An error
  swallowed on a path that loses a file is not low. Concrete instances: a
  success response that hides a failure — an empty result returned as if real
  while a count or flag says otherwise; a cleanup path that drops the record
  and leaves the data, or the reverse; and an error path that loses the only
  copy.
- **Exposure floor.** A secret or credential exposure finding, or an authorization
  boundary reached without the caller's scope check, is always `high`, whatever the
  reviewer's confidence.

Any high **or** medium finding blocks (Fix required); low never blocks. When
unsure between two levels, state the doubt rather than inflating. Uncertainty
about severity is never grounds for omitting a finding: where you cannot
place one, report it at your best estimate and say the estimate is
uncertain — a defect you can describe is a defect you report.

### 8. Check test coverage, rolled up per cohort
Ask of **every** finding you write, at **every** severity: would an existing
test fail if this defect regressed? Then roll the answers up — raise **one**
`test-coverage` finding per cohort that has uncovered findings (see
`${CLAUDE_PLUGIN_ROOT}/skills/review/references/json-output.md` for the shape),
naming each defect it would guard and where the tests belong. Never one per
finding: that multiplies with the findings themselves and buries the defects
it was meant to flag. A cohort whose findings are all covered raises none.
Anchor the roll-up once, where the tests belong — it reports a gap spanning
sites, not a defect at each.

## Presentation (human mode — the default)

1. **Effort score (1–5) at the top**, derived from the diff summary counts
   (files, languages, hunks, kinds, `signature_changes`) plus cohorts touched —
   and, in spec-aware mode, task count and unmet-scenario count. 1 = trivial;
   3 = moderate (several files/cohorts or a signature change); 5 = complex.
   State the number with a one-line justification citing the counts.
2. **Resolved endpoints — directly under the effort score.** State the base,
   head, and merge base (where the mode carries one) as commit ids — the
   engine's `base_sha`, `head_sha`, and `merge_base` — before any findings,
   so a reader sees exactly which commits produced them. In working-tree mode
   the `merge_base` is the before side, not `base_sha`.
3. **Findings header — directly below the endpoints line.** A line
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
4. **Summary table** — one row per finding, most-severe first, columns
   `# | rating | details`; rating is 🔴 high / 🟠 med / 🟡 low (display label
   `med`; the severity value stays `medium`). No findings → print
   `## Findings: ✅ Ship it` and "No problems found." and omit the empty
   table. `review_gate.py post` closes the summary comment with one stat
   line, `Reviewed N files, +A -D lines.`, counted from the PR's own file
   list — the review body you write carries no such line.
5. **Collapsible walkthrough** in `<details><summary>Walkthrough</summary>`.
6. **Diagrams — only when structurally warranted.** Mermaid: sequence for
   API/flow changes, ER for schema/data-model, state for lifecycle logic.
   Emoji-free labels. Dark-mode-safe: any colour must be low-alpha `rgba()`
   (~0.05–0.15), never opaque pastel fills; never hard-code label text colour;
   never rely on colour alone — label bands as text.
7. **Findings by cohort** — reuse the summary table's numbers — then the
   **verdict** and an explicit list of **what you could not verify**.

## Degradation

Difftastic is required. `semdiff diff` exits non-zero without it rather than
completing on a text engine nobody can audit; only a single file whose own
difft output fails to parse still falls back to the text engine for that file
alone, stamping `engine: "text"` on its entry.

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
  - **Still missing** → **stop.** Do not run `diff`, `files`, or any analysis.
    Report prominently, before anything else, that difftastic is required and
    could not be installed, the manual install hint (e.g.
    `brew install difftastic`), and that no verdict was produced.

Whenever a single file falls back to the text engine through its own difft
parse failure, say so and record it as a could-not-verify entry — in the human
mode's "what you could not verify" list *and* in `--json`'s `could_not_verify`
array — naming that file's text-engine fallback. `doctor` (without `--fix`)
reports what is available and touches nothing. git and difft are the two hard
requirements.

## Documentation standard

Both the rendered report (Presentation, above) and the posted summary comment
(`review_gate.py post`) are bound to the shipd documentation standard at
`${CLAUDE_PLUGIN_ROOT}/skills/document/references/standard.md`. That file is
the one canonical source of its rules — this section restates none of them;
read it directly. Name one reported defect a **finding** throughout, in the
report, the summary comment, and `--json` — never "issue" or "concern".

## Guardrails

- **Emoji at exactly the four sanctioned sites** — the ☕ brand-line mark, the
  ✅/❌ verdict marker, the 🔴/🟠/🟡 severity dots in the summary table, and
  that same dot prefixing a severity wherever a posted finding names it: an
  anchored inline comment's leading marker, and each folded-findings bullet.
  Nowhere else: not in prose, findings, other tables, or mermaid labels. The
  `--json` output (json-output.md) carries none.
- **Read-only, except the base-freshness fetch.** The review never edits the
  repo — the review-start fetch (see Base freshness, above) writes
  remote-tracking refs only, never the working tree, the index, or a local
  branch, and the skill never pulls, rebases, or checks anything out.
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
