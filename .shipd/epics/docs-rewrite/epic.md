# docs-rewrite
Status: complete
Theme: developer-experience

## Introduction

The `docs/` tree has grown to ~2,900 lines across 15 files with no shared
writing standard, and one file (`copilot-review.md`) alone runs 711 lines.
Meanwhile the strategic focus has moved to workspaces, but the docs still
present workspaces as one topic among many. The shipd documentation standard
now exists (`/s:document`, plugin v0.6.202) and nothing under `docs/` conforms
to it yet.

This epic rewrites the whole tree through `/s:document`: every doc classified,
trimmed to its cap, and linted clean, with the workspaces cluster promoted to
the flagship position and the enterprise teams layout documented. A CI gate
lands first and grows with the rewrite, so a rewritten doc can never regress.

Success criteria: every doc under `docs/` (retros excepted) carries a doc-type
marker and passes `docs_lint.py`; the CI gate enforces that on every PR; the
entry path reads what-is-shipd → getting-started → cheatsheet; the workspaces
cluster leads the tree and carries the enterprise layout.

### Non-goals

- No changes to the standard, the lint, or the `/s:document` skill — they are
  fixed inputs; a defect found in them becomes its own change outside this
  epic.
- No rewrite of `docs/retros/` — retros are dated historical records and stay
  exempt from the standard and the lint.
- No new feature documentation — the epic rewrites what exists; docs for
  future features arrive with those features.
- No README.md or AGENTS.md restructure — members touch them only to fix
  links into `docs/`.

## Decisions

- **Every rewrite runs through `/s:document`.** The skill loads the canonical
  rules file (`plugins/s/skills/document/references/standard.md`) and gates on
  `docs_lint.py`; no member hand-writes docs prose outside it.
- **Marker-gated CI first, full enforcement last.** The first member adds a CI
  step linting only the docs that carry a doc-type marker, so each rewritten
  doc opts in as it ships and cannot regress mid-epic. The final member flips
  to full scope: every file under `docs/` except `retros/` must carry a marker
  and pass. Rejected: one full gate at the end — it leaves rewritten docs
  unguarded for the epic's whole duration.
- **The entry docs merge.** `quickstart.md` is deleted; `getting-started.md`
  becomes the single how-to (≤150 lines): install → doctor → onboard → first
  plan/build → board. The entry path is `what-is-shipd.md` (concept) →
  `getting-started.md` (how-to) → `cheatsheet.md` (reference). Rejected:
  keeping both — they duplicate the same walk and split maintenance.
- **Workspaces lead the tree.** `docs/workspaces.md` plus `docs/workspaces/`
  is the flagship cluster: `what-is-shipd.md` and `README.md` link it first,
  and its docs are rewritten as the model of the standard. The enterprise
  guidance extends `teams.md`: a dedicated workspaces repository holding one
  folder per team or group, each folder a job workspace, following the
  member-map and partial-materialization mechanics that already exist.
- **A doc over its cap splits by type.** `copilot-review.md` becomes a how-to
  (install and enable, ≤150) plus a reference (verbs, flags, limits, ≤250).
  `prd.md` (336 lines) is re-classified and trimmed or split the same way at
  planning time. No cap exception is ever granted.
- **One doc, one type, one job.** Each member assigns every touched doc
  exactly one `doc-type` marker; content that belongs to another type moves to
  the doc of that type rather than stretching the cap.
- **Diagrams obey the structural test.** At most one mermaid diagram per doc,
  only where it carries a topology, a branched lifecycle, or three or more
  interacting components; a member deletes decorative diagrams it inherits.

## Design

The epic is a pipeline with a guarded middle. The first member installs the
marker-gated CI step, the four rewrite members then convert the tree cluster
by cluster in any order, and the final member flips the gate to full scope
once every cluster conforms.

The four rewrite clusters follow the tree's natural seams: the workspaces set
(the flagship, six files today), the entry set (four files becoming three),
the copilot-review split (one file becoming two), and the feature guides
(oracle, prd, guardrails, supersession-gate). Each member classifies its docs,
rewrites them through `/s:document`, adds the markers, fixes inbound links
(`README.md`, `AGENTS.md`, and cross-doc links), and ships with the CI gate
already checking its output. Because the gate is marker-scoped, clusters land
independently and nothing blocks on sibling clusters.

The final member sweeps: it confirms every remaining file carries a marker,
switches the CI step from marker-scoped to full-scope (all of `docs/` minus
`retros/`), and fixes anything the sweep surfaces.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| docs-lint-gate | Add the marker-gated docs-lint step to `ci.yml`, scoped to docs carrying a doc-type marker; `retros/` exempt | low | low | low | low |
| docs-workspaces-rework | Rewrite `workspaces.md` + `docs/workspaces/` to the standard, workspaces-first, extending `teams.md` with the enterprise one-folder-per-group layout | medium | medium | medium | low |
| docs-entry-merge | Rewrite `what-is-shipd.md` and `cheatsheet.md`; merge `quickstart.md` into `getting-started.md` and delete it; fix entry links | low | medium | low | low |
| docs-copilot-review-split | Split the 711-line `copilot-review.md` into a how-to and a reference, each under its cap | low | low | medium | medium |
| docs-feature-guides | Rewrite `oracle.md`, `prd.md`, `guardrails.md`, `supersession-gate.md` to the standard; re-classify or split `prd.md` | low | low | low | low |
| docs-full-enforcement | Flip the CI gate to full scope over `docs/` (minus `retros/`); sweep and fix any straggler | low | low | low | low |

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 73 | 18.0k |
| Write | 1 | 6.5k |
| Edit | 10 | 2.8k |
| Read | 31 | 1.9k |
| SendMessage | 3 | 1.1k |
| Monitor | 3 | 731 |
| Agent | 3 | 721 |
| ToolSearch | 5 | 398 |
| (no tool) | 0 | 229 |
| TaskStop | 2 | 74 |
| **Total** | 131 | 32.5k |
