# docs-copilot-review-split
Status: verified
Epic: docs-rewrite
Theme: developer-experience

## Idea

Split the 711-line `docs/copilot-review.md` into a how-to and a reference,
each conforming to the shipd documentation standard and its line cap.

### Motivation

`docs/copilot-review.md` runs 711 lines with no doc-type marker and fails
`docs_lint.py` (observed: exit 1), while every documentation cap tops out at
250 lines. The approved `docs-rewrite` epic assigns this member its split by
type — a how-to (≤150) plus a reference (≤250) — under the marker-scoped CI
gate already in `.github/workflows/ci.yml`.

### Details

- `docs/copilot-review.md` becomes the how-to (marker `how-to`, ≤150 lines):
  prerequisites, install, enable, the reviewer-token recipe, verify,
  upgrade/uninstall.
- A new `docs/copilot-review-reference.md` (marker `reference`, ≤250 lines)
  takes the managed-file inventory, the gate's two reviewer modes, the
  verdict classification, the strictness knob, the trust boundary, the
  report states, and scope and limits.
- One delta spec modifies `project-readme`'s `copilot-review-guide`
  requirement into the two-doc contract.
- `docs/guardrails.md`'s See-also link is retargeted to the new how-to title.

Affected capabilities: `project-readme` (modified). Impact:
`docs/copilot-review.md`, `docs/copilot-review-reference.md` (new),
`docs/guardrails.md` (one link line). No engine, plugin, or CI changes.

### Non-goals

- No changes to the standard, the lint, the `/s:document` skill, or the CI
  step — fixed inputs per the epic.
- No plugin edits: `plugins/s/skills/doctor/SKILL.md` and the gate workflow
  template keep their `docs/copilot-review.md` pointers, which stay valid.
- No behavior changes — every documented claim survives the restructuring or
  drops as a duplicate; no re-derived facts.
- No full-scope gate flip (the `docs-full-enforcement` member) and no edits
  to sibling clusters' docs beyond the one `guardrails.md` link line.

## Implementation

**Target classifications (binding):**

| file | type | cap |
| --- | --- | --- |
| `docs/copilot-review.md` | how-to | 150 |
| `docs/copilot-review-reference.md` (new) | reference | 250 |

**Naming follows the sibling precedent.** `docs-feature-guides` shipped
`prd.md` + `prd-reference.md`, so the reference lands at
`docs/copilot-review-reference.md`. Rejected: a `docs/copilot/` subfolder —
one extra level for two files, and no sibling uses one.

**The how-to keeps the path and the token recipe.** The verified `shipd-gate`
and `shipd-doctor` specs pin the minimal-PAT recipe to
`docs/copilot-review.md`, so the how-to stays at that path and carries the
full recipe: the dedicated fine-grained PAT with no repository access and
only the "Copilot Requests" permission, the broad-scope warning, `gh secret
set COPILOT_GITHUB_TOKEN`, bounded expiry with fail-safe semantics, and
removal restoring the poll fallback. The `/s:doctor` skill's pointer to the
recipe therefore stays valid with no plugin edit.

**Content moves, it is not re-derived.** The how-to keeps, in task order:
prerequisites (paid Copilot plan, GitHub hosting, `shipd` on PATH); the
`/s:gate` shortcut note; `shipd copilot add` with its output and `--root`;
the four managed file paths named briefly; commit-and-push with the
head-branch rule and the changed-skill-reviews-itself consequence scoped to
the CCR/poll surface; enabling reviews per-PR and via a branch ruleset (and
that the CLI reviewer mode needs neither); the token recipe; verification via
`shipd doctor`'s `protection`/`automerge`/`copilot-secret` lines and the bare
`shipd copilot` report; re-`add` as the upgrade, `remove` as the uninstall,
and edit-the-template-not-the-copy. The reference takes: the managed-file
table with each file's role; the two-mode comparison table and the
pending-first rule; the CLI reviewer run sequence (pinned CLI version,
base-ref-materialized instructions, timeout, pending on failure, private-repo
support, credit cost, concurrency cap); the poll fallback (why it polls, the
fail-open guarantee with the disabled bash tool, the 20-second/15-minute
bounds, timeout semantics, runner cost); the verdict table with the
last-line-only rule; `SHIPD_GATE_FAIL_OPEN` with the `gh variable set` path,
the variable-not-edit rule, and the pair-with-token guidance; the trust
boundary (baseline, residual risk, the bounded mitigations including the
posting step's `GITHUB_PATH`/`GITHUB_ENV` insulation and its limits, the
session flow as the high-assurance path); tokens and permissions with the
fork-PR limit and session-flow coexistence; the poll-scoped private-repo note
with the fail-soft setup workflow; the report states table, ownership
markers, and foreign/`--force`; and scope and limits (no model selection,
relevance-driven pickup, optional difft/ripgrep, read-only review). The
retracted-bootstrap history compresses to one line: the installing pull
request is gated by the gate it installs.

**Cross-links.** The how-to opens with a link to the reference (mirroring
`prd.md` → `prd-reference.md`) and the reference opens with a link back. The
how-to's See-also keeps `/s:review` and the doc-relative research report link
(target `.shipd/research/copilot-code-review/report.md` — observed
present). `docs/guardrails.md:217` retargets its link text to the how-to's
new title; guardrails.md must still lint clean after the edit.

**Diagrams.** Neither doc gets one. The two-mode comparison is a table, and a
mermaid restating it would fail the standard's no-restating rule. The old doc
carried none to inherit.

**No plugin edits — accepted one-hop staleness.** The gate template's comment
(`plugins/s/integrations/copilot/copilot-review-gate.yml:116`) says the doc
states the trust boundary "in full"; after the split the how-to links to the
reference's trust-boundary section, one hop away. Rejected: editing the
template — a comment-only change forces a plugin version bump and marks every
install `stale`.

**Risks.** The reference's 250-line cap must hold every obligation the
`copilot-review-guide` requirement pins; the guard is reference style — terse
lists and the four tables — plus the delta's scenarios, which enumerate the
obligations so the lint-and-trim loop cannot silently drop one. The how-to's
150 cap is looser: today's corresponding sections compress well under it.
