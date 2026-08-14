# epic-intro
Status: verified
Theme: developer-experience

## Idea

The first real epic exposed a readability problem: an epic opens cold with a
dense `## Decisions` list, so a reader gets binding architectural choices
before they know what the feature is or why it exists. The user flagged it
directly, and the industry guidance agrees — well-written epics (Atlassian,
Aha!, Microsoft's engineering playbook, Bridging the Gap) open with a
narrative overview: the problem and motivation, the goal, and measurable
success criteria, with scope boundaries stated explicitly, before any
technical content.

This change restructures the epic document:

- `## Introduction` becomes a required section and MUST be the first level-2
  section: the why (problem and motivation) first, then the what (the feature
  in brief) and the intended outcome/success criteria, closing with a
  required `### Non-goals` subsection — the same why-first grammar `plan.md`'s
  Idea already uses, so authors keep one mental model.
- Section order is Introduction → Decisions → Design → Changes.
- `lint_epic` enforces the new section and its position; the `/s:epic` skill
  template, `am/README.md`, and the existing `am/epics/workspace-projects/`
  epic migrate in this same change so library lint and CI stay green.
- Plugin version bump 0.1.8 → 0.1.9.

### Non-goals

- No change to `plan.md`'s structure — only the epic artifact.
- Success criteria stay authoring guidance inside the Introduction, not a
  lint-enforced subsection — enforcement stays structural, not editorial.
- No new sections beyond Introduction (no Dependencies/Open Questions/etc.
  from the heavyweight templates — epics stay lean; Decisions and Design
  already carry that content where it matters).
- No epic status or stub-table changes.

Affected capabilities: `shipd-spec-format` (modified `epic-artifact-layout`),
`shipd-epic` (modified `epic-interview-skill`). Impact:
`plugins/s/skills/build/scripts/{spec_common,spec_lint}.py` and their tests,
`plugins/s/skills/epic/SKILL.md`, `am/README.md`,
`am/epics/workspace-projects/epic.md` (migrated in place),
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Mirror the plan grammar, don't invent a new one.** The Introduction
  follows `plan.md`'s Idea rules — why before what, required `### Non-goals`
  heading — so one editorial convention covers both artifacts. Rejected: a
  free-form summary paragraph with no enforced heading (regresses to unlinted
  prose and loses the non-goals discipline the research singles out as the
  highest-value line).
- **Position is enforced, not just presence.** `## Introduction` must be the
  *first* level-2 section in the document; presence-only would allow it to be
  appended after `## Changes`, which defeats the purpose. Implementation: in
  `spec_common.py`, extend the epic section constant (the tuple `lint_epic`
  checks) to `("## Introduction", "## Decisions", "## Design", "## Changes")`
  and add a first-section check in `lint_epic` in `spec_lint.py`: the first
  line matching `^## ` must be `## Introduction`, and `### Non-goals` must be
  present. Order among the remaining three sections stays unenforced,
  matching how plan sections are handled today.
- **Migration ships in the same change.** The new lint rule would fail the
  existing `workspace-projects` epic, so this change edits that epic in place
  (epics are mutable, unlike `am/completed/` archives) — its Introduction
  content is fixed in the task text so the executor exercises no judgment.
  Sequencing inside the change: lint fixtures are self-contained temp roots,
  so engine tasks pass before the migration; the real-repo library lint runs
  in the verification barrier after migration.
- **Skill and docs follow the format authority.** `plugins/s/skills/epic/
  SKILL.md`'s epic contract template gains the Introduction (with its element
  order and the success-criteria guidance), and `am/README.md`'s Epics
  section documents the new required section and ordering rule.
- **Risk:** any third-party epic authored against 0.1.8 breaks on the new
  rule. Accepted — the epic layer shipped hours ago and the only existing
  epic migrates here; better to tighten before adoption spreads.
