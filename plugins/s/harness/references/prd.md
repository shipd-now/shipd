# /s:prd reference — the PRD contract

Author into a staging file (a `mktemp` path is fine) and let
`spec_emit.py prd` install it. Never construct the workspace path yourself.

```
# <prd-slug>
Status: draft
Template: standard
Initiative: <initiative-slug>    (optional — only a brief that resolves)

## Problem

<what is broken today, who feels it, and why now>

## Solution

<what gets built, and the shape of it>

...one section per entry in the tier's list below, in that order...
```

## Rules the linter enforces

- **Title.** `# <slug>` matches the PRD's directory name.
- **Status.** One of `draft`, `approved`, `superseded`, in the first five
  non-blank lines. A new PRD is `draft`; approval is a re-install carrying
  `Status: approved`, never a hand-edited header.
- **Template.** One of `basic`, `standard`, `comprehensive`, in the first five
  non-blank lines. An absent or unknown tier is an error — nothing is defaulted.
- **Metadata.** `Initiative:` is the only other recognized key: a kebab-case
  slug naming an initiative brief that resolves across the workspace chain.
  Omit the line entirely when the PRD has no parent initiative.
- **Sections.** Every section its declared tier requires must appear as an
  exact level-2 heading. Sections beyond the tier's list are allowed.

## The tiers, nested additively

- **`basic`** — `## Problem`, `## Solution`, `## Success criteria`.
- **`standard`** (the default) — `basic`'s three, then `## Users`,
  `## Requirements`, `## Non-goals`.
- **`comprehensive`** — `standard`'s six, then `## Risks`, `## Rollout`,
  `## Open questions`.

Because the tiers nest, a mid-interview escalation only adds sections to cover,
and a de-escalation keeps the extra answers as allowed extra sections.

## Where the work lands

A PRD lives at `<workspace-root>/<content-dir>/prds/<slug>/prd.md`, resolved by
the engine across the workspace chain — outside the repository, so the repo's
worktree-and-PR workflow does not apply. Install with
`spec_emit.py prd <slug> --from <staging-file>` (`--replace` to overwrite an
existing one); it validates in process and, on any finding, restores what it
replaced and exits non-zero, so a failed install leaves the store untouched.
Read the installed document back with `spec_status.py cat prd <slug>`.
