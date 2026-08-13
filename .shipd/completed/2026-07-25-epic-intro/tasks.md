# Tasks — epic-intro

## 1. Lint enforcement

- [x] 1.1 [req: epic-artifact-layout] Add failing tests in
      `plugins/s/skills/build/tests/test_spec_lint.py` (temp-root fixtures):
      an epic with Introduction (containing `### Non-goals`) → Decisions →
      Design → Changes passes `--epic` lint; an epic missing
      `## Introduction` errors; an epic whose first level-2 section is
      `## Decisions` with `## Introduction` appearing later errors; an
      Introduction without `### Non-goals` errors. Update any existing epic
      fixtures that use the old Decisions-first structure so the rest of the
      suite still exercises what it did before. Run and observe the new
      tests fail.
- [x] 1.2 [req: epic-artifact-layout] In
      `plugins/s/skills/build/scripts/spec_common.py`, extend the epic
      required-sections constant to
      `("## Introduction", "## Decisions", "## Design", "## Changes")`; in
      `lint_epic` in `plugins/s/skills/build/scripts/spec_lint.py`, add the
      first-section check (the first line matching `^## ` must be
      `## Introduction`) and the `### Non-goals` presence check. Confirm the
      1.1 tests pass.

## 2. Migration, skill, and docs

- [x] 2.1 [P2] [req: epic-artifact-layout] Migrate
      `am/epics/workspace-projects/epic.md`: insert the following section
      verbatim between the header metadata block and `## Decisions` (leave
      every existing section untouched), then confirm
      `python3 plugins/s/skills/build/scripts/spec_lint.py --epic workspace-projects`
      exits 0:

      ```
      ## Introduction

      Shipd's Initiative → Epic → Change hierarchy is only two-thirds
      real: epics and changes exist, but an initiative is still just a
      validated slug with nothing behind it, and nothing groups the repos an
      initiative spans. This epic builds the workspace layer: workspace
      discovery (`.shipd/workspace.json` as marker and registry),
      initiative briefs that track outcomes as tickable requirements,
      projects that group repos with steering context to focus planning, and
      an `/s:initiative` skill driving it all.

      Success criteria: a brief can be created, listed, reviewed
      (requirements ticked), and attached to an epic; `Initiative:`
      references resolve against the workspace when one is present while
      bare-checkout CI stays green; a workspace with no declared projects
      behaves exactly as a single implicit project.

      ### Non-goals

      - No sync or projection of briefs to any central service.
      - No cross-repo build orchestration — the workspace focuses planning,
        not execution.
      - No changes to the epic or change artifact formats.
      ```
- [x] 2.2 [P2] [req: epic-interview-skill] Update the epic contract in
      `plugins/s/skills/epic/SKILL.md`: the template shows
      `## Introduction` (why first, then the what and intended outcome,
      success criteria recommended, closing `### Non-goals`) as the first
      section ahead of Decisions/Design/Changes, and the authoring flow
      mentions drafting it before the other sections.
- [x] 2.3 [P2] [req: epic-artifact-layout] Update the Epics section of
      `am/README.md`: document `## Introduction` as the required opening
      section (element order: why, what/outcome with success criteria
      recommended, `### Non-goals`), and the Introduction-first ordering
      rule.
- [x] 2.4 [P2] [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.1.8` → `0.1.9`.

## 3. Verification

- [x] 3.1 [req: *] Run the full engine test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`),
      library lint (`python3 plugins/s/skills/build/scripts/spec_lint.py`,
      which now validates the migrated epic),
      `python3 plugins/s/skills/build/scripts/spec_lint.py --epic workspace-projects`,
      and `python3 plugins/s/skills/build/scripts/spec_lint.py epic-intro`;
      everything green.
