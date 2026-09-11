# docs-entry-merge
Status: verified
Epic: docs-rewrite
Theme: developer-experience

## Idea

Rewrite the entry documentation to the shipd documentation standard: merge
`docs/quickstart.md` into `docs/getting-started.md` and delete it, rewrite
`docs/what-is-shipd.md` and `docs/cheatsheet.md` in place, and fix every
inbound entry link.

### Motivation

The entry path duplicates one walkthrough across `quickstart.md` (174 lines)
and `getting-started.md` (240 lines), and none of the four entry docs carries
a doc-type marker or passes `docs_lint.py`. The approved `docs-rewrite` epic
decides the merge and the entry path: `what-is-shipd.md` (concept) →
`getting-started.md` (how-to) → `cheatsheet.md` (reference).

### Details

- `docs/getting-started.md` becomes the single entry how-to (≤150 lines):
  install → doctor → onboard → first `/s:plan` and `/s:build` → watch
  (board, status, statusline). `docs/quickstart.md` is deleted.
- `docs/what-is-shipd.md` is rewritten to the concept type (≤100 lines),
  keeping its pinned diagram, ☕ title, and closing paragraph.
- `docs/cheatsheet.md` is refreshed to parity with `plugins/s/skills/` and
  the `shipd --help` banner, as its verified requirement already demands.
- Inbound links retarget: `README.md:250`, `docs/copilot-review.md:25`, and
  cross-links among the entry docs.

Affected capabilities: `project-readme` (modified), `shipd-install`
(modified). Impact: the four entry docs, `README.md`, one link line in
`docs/copilot-review.md`. No engine or plugin code changes.

### Non-goals

- No changes to the standard, the lint, the `/s:document` skill, or the CI
  step — fixed inputs per the epic. `plugins/s/skills/document/SKILL.md`'s
  example string naming `docs/quickstart.md` stays untouched.
- No rewrite of `docs/copilot-review.md` beyond its one quickstart link —
  the split belongs to the `docs-copilot-review-split` member.
- No changes to the workspaces cluster, `docs/retros/`, or the feature
  guides; no README restructure beyond the entry-link section.
- No behavior changes — the docs document what exists; stale claims are
  corrected only against observed command output.

## Implementation

**Target classifications (binding):**

| file | type | cap |
| --- | --- | --- |
| `docs/what-is-shipd.md` | concept | 100 |
| `docs/getting-started.md` | how-to | 150 |
| `docs/cheatsheet.md` | reference | 250 |

**The `/s:document` flow governs every rewrite.** Read
`plugins/s/skills/document/references/standard.md` first; put the marker on
line 1; run `python3 plugins/s/skills/document/scripts/docs_lint.py <file>`
after each rewrite and fix findings until it exits 0. Observed: the lint
enforces the marker, the per-type line caps, sentence-length caps, and
passive-voice warnings (`docs_lint.py docs/what-is-shipd.md` exits 1 today
with exactly those findings).

**Merged getting-started shape (binding).** Title "Getting started". Six
numbered steps in quickstart's order — the epic's decided walk:

1. Install — the `curl -fsSL https://shipd.now/install | sh` one-liner, the
   PATH note, auto-update enablement with apply semantics plus `shipd update`
   (`--check` as report-only) and `claude plugin update s@shipd` as manual
   fallbacks, and the harness selection with its headless degradation and
   `shipd harness add` for repo-level installs.
2. Preflight — `shipd doctor`, listing the checks the verb reports (observed:
   `python`, `git`, `config`, `pipeline`, `schema`, `wiki`, `gh`, `difft`,
   `textual`, `snapshot`, `statusline`, `protection`, `automerge`,
   `copilot-secret`), the `warn` vs `fail` semantics, the
   `{"autonomous-pipeline": "eco"}` opt-in line, and the `{"pr-mode":
   "draft"}` line.
3. Tour — `/s:onboard`, resumable state, sandbox safety.
4. Plan — `/s:plan` with the worktree it creates and the artifact set at
   purpose level: `plan.md` (decisions), `specs/<capability>/spec.md` (the
   testable delta), `tasks.md` (the checklist). Link `.shipd/README.md` as
   the grammar authority instead of fenced excerpts — the 150-line cap and
   the one-doc-one-job rule route grammar detail there. Rejected: keeping
   the excerpt blocks — they alone cost ~40 lines.
5. Build — `/s:build`, verification against the delta scenarios, and the
   three durable outcomes: the `change/<name>` branch, the `verified/`
   merge, the `completed/` archive.
6. Watch — `shipd board`, `shipd status`, `shipd list`, and statusline
   registration via `shipd statusline install`, stating that the written
   entry resolves the newest cached snapshot rather than a version-pinned
   path. Rejected: reproducing the manual `statusLine` JSON block — the cap
   pressure and `shipd statusline install` writing that exact shape make it
   redundant.

Close with a where-to-next list linking `cheatsheet.md`, `what-is-shipd.md`,
and `workspaces.md`. Statusline placement follows quickstart's step-6 model;
the old statusline deep-dive is cut, not moved.

**what-is-shipd rewrite (binding).** Keep the `<!-- doc-type: concept -->`
marker as line 1, the ☕-opening level-1 title, the `flowchart TD` mermaid
fence verbatim, and the "Today shipd builds itself" paragraph as the closing
prose — all pinned by `readme-brand-marks` and `what-is-overview-layout`,
which this change does not modify. Rewrite the prose to the sentence caps and
add one forward link to `getting-started.md` in the prose before the diagram
(nothing may follow the closing paragraph).

**cheatsheet refresh (binding).** Rebuild the `/s:` table from the directory
listing of `plugins/s/skills/` (24 skills today — `document`, `explain`,
`prd`, and `worktree-hooks` are missing rows) and the CLI table from the
`shipd --help` banner (observed verbs: `init`, `list`, `status`, `locate`,
`related`, `search`, `epic`, `prd`, `workspace`, `wiki`, `config`, `board`,
`render`, `metrics`, `lint`, `worktree`, `doctor`, `statusline`, `copilot`,
`vendor`, `harness`, `install`, `update`). Keep the conventions preamble;
keep the `workspace` row's precondition note; read-only examples must run
and exit 0 from the repo root.

**Link fixes (binding).** `README.md`'s "## Quickstart" section becomes
"## Getting started" and links `docs/getting-started.md` (still before the
engine internals; the flagship ordering of `readme-workspaces-flagship-link`
is untouched). `docs/copilot-review.md:25` retargets to
`getting-started.md#1-install` — the merged doc keeps the `## 1. Install`
heading so that anchor resolves. After the delete, no file under `docs/`
(retros exempt) and no line of `README.md` may reference `quickstart.md`.

**Risks.** The 150-line cap on the merged doc is the tight constraint; the
guard is the step budget above and cutting excerpts/deep-dives rather than
obligations — every clause of the modified requirements maps to one step.
Anchor drift is the second risk; the guard is pinning the `## 1. Install`
heading and re-running the repo-wide grep in verification.
