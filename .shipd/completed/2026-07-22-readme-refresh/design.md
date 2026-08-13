## Context

`README.md` has a spec contract (`project-readme` capability): banner first,
skills cataloged, onboarding retained. The repo has since gained the spec
engine (shipd-spec-format/lint/merge), the plan and status skills, the status
pipeline, and the statusline. This change updates the contract and the file.

## Goals / Non-Goals

**Goals:**
- A reader with no context understands what the repo is, what the three
  skills do, how a change flows draft → verified, and what the statusline
  shows — from the README alone.
- Every claim in the README matches the current code and paths.

**Non-Goals:**
- No restating of the full requirement/delta grammar (link to
  `am/spec/README.md`, the format authority, instead).
- No screenshots or generated content; plain markdown only.
- No changes to the banner (fixed by its own requirement).

## Decisions

### D1 — Section order and content
Keep the existing skeleton and extend it: banner → one-line intro → **Skills**
(table, three rows) → **The spec engine** (new: am/spec layout tree, change
artifacts, lifecycle diagram line `draft → ready → active → complete →
verified` with one sentence per stage, guarded transitions + `--force`,
pointer to `am/spec/README.md` for the grammar) → **Statusline** (new: what it
renders, `☢️ <name> · <status> · <done>/<total>`, selection via
`spec_status.py use`, registration snippet from `.claude/settings.json`) →
**Build telemetry** (new, short: report table, `~/.shipd/config.json` keys,
`builds.jsonl`) → **Structure** (updated tree) → **Install** → **Adding a
command** → **Adding a skill** → **After editing**. Existing wording is
preserved where still true (per the retained-onboarding requirement).

### D2 — Skill descriptions come from the skills' own frontmatter
Each Skills-table row paraphrases the skill's `description` frontmatter in
`plugins/s/skills/<name>/SKILL.md` (source of truth), one to two sentences,
naming the invocation (`/s:plan`, `/s:build`, `/s:status`). The build row
describes the tier policy (plans on the strongest model, executes one tier
below) without naming concrete models.

### D3 — Accuracy is checked against the repo, not memory
The rewrite task requires verifying, before completion: the skills table
matches `ls plugins/s/skills/`; every path named in the Structure tree
exists; the statusline line format matches `statusline.sh`; the config keys
match `shipd.config.example.json`; and no `openspec` reference remains in
the README.

## Risks / Trade-offs

- **Docs drift again as skills evolve** → the `project-readme` capability now
  encodes the three-skill catalog and engine documentation as requirements, so
  future skill changes that touch the catalog surface in spec deltas.
- **README length** → mitigated by linking to `am/spec/README.md` for grammar
  details rather than duplicating them.
