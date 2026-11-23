# Tasks — docs-epics-group

Every writing task follows `plan.md` §Implementation: read
`plugins/s/skills/document/references/standard.md` first, write the page
through the `/s:document` flow, keep the three exact level-2 headings `## When to use it`, `## How to run it`, and `## Reference` in order, and
link only the files `plan.md` names under "Links".

## 1. Write the epic pages

- [x] 1.1 [req: epics-user-docs] Create `docs/epics.md` with
      `<!-- doc-type: how-to -->` as line 1 and the title "Epics". Take the
      facts from `plugins/s/skills/epic/SKILL.md` (amend mode at "Amend
      mode", the artifact at "The epic contract", the run at "Flow" and
      "Ending") and `plugins/s/skills/explain/SKILL.md`. Cover every item
      the `epics-user-docs` requirement lists, and close with the
      `## Reference` table of the three skill invocations and the four
      `shipd` verbs. Add no mermaid fence. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/epics.md`
      and fix findings until it exits 0 at 150 lines or fewer.
- [x] 1.2 [req: epic-grill-user-docs] Create `docs/epic-grill.md` with
      `<!-- doc-type: how-to -->` as line 1 and the title "Epic grill". Take
      the facts from `plugins/s/skills/epic-grill/SKILL.md`. Cover every
      item the `epic-grill-user-docs` requirement lists, with the run as
      numbered steps in the skill's section order, and close with the
      `## Reference` table for `<epic>` and `--parallel N`. Add no mermaid
      fence. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/epic-grill.md`
      and fix findings until it exits 0 at 150 lines or fewer.

## 2. Write the delivery pages

- [x] 2.1 [req: autopilot-user-docs] Create `docs/autopilot.md` with
      `<!-- doc-type: how-to -->` as line 1 and the title "Autopilot". Take
      the facts from `plugins/s/skills/autopilot/SKILL.md` ("Mode
      selection", "Phase 1", "Phase 2", "Failure contract: park and
      continue", "Resuming an interrupted run", "The in-session run
      summary", "Phase 3", "Phase 4"). Cover every item the
      `autopilot-user-docs` requirement lists. Add exactly one mermaid
      `flowchart` showing one member's path: plan, gate, build, pull
      request, with a parked branch off a failed stage and a blocked branch
      for an unmerged `After` dependency. Close with the `## Reference`
      controls table and the list of seven park reasons. Name the live view
      as `shipd board --epic <epic>`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/autopilot.md`
      and fix findings until it exits 0 at 150 lines or fewer.
- [x] 2.2 [req: drift-user-docs] Create `docs/drift.md` with
      `<!-- doc-type: how-to -->` as line 1 and the title "Drift". Take the
      facts from `plugins/s/skills/drift/SKILL.md`. Cover every item the
      `drift-user-docs` requirement lists, with one example
      `## Drift verdicts` block inside a code fence, and close with the
      `## Reference` tables for the verdicts and the finding kinds. Add no
      mermaid fence. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/drift.md`
      and fix findings until it exits 0 at 150 lines or fewer.

## 3. Write the initiatives page

- [x] 3.1 [req: initiatives-user-docs] Create `docs/initiatives.md` with
      `<!-- doc-type: how-to -->` as line 1 and the title "Initiatives".
      Take the facts from `plugins/s/skills/initiative/SKILL.md`. Cover
      every item the `initiatives-user-docs` requirement lists, with one
      example brief inside a code fence, and close with the `## Reference`
      table of the four verbs plus `shipd workspace` and
      `shipd lint --initiative <slug>`. Add no mermaid fence. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/initiatives.md`
      and fix findings until it exits 0 at 150 lines or fewer.

## 4. Verify

- [x] 4.1 [req: *] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/epics.md docs/epic-grill.md docs/autopilot.md docs/drift.md docs/initiatives.md`
      and confirm exit 0. Confirm `wc -l` reports each of the five files at
      150 or fewer. Confirm every relative link in the five files resolves
      to an existing file under `docs/`. Confirm
      `grep -n 'spec_status\|spec_emit\|spec_lint\|spec_gate\|autopilot\.py\|dashboard\.py' docs/epics.md docs/epic-grill.md docs/autopilot.md docs/drift.md docs/initiatives.md`
      matches nothing. Confirm `grep -c '```mermaid'` reports 1 for
      `docs/autopilot.md` and 0 for the other four. Confirm
      `git status --short` lists only the five new files outside `.shipd/`.
      Run `plugins/s/bin/shipd lint docs-epics-group` and confirm it reports
      the change clean.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 137 | 50.2k |
| Write | 15 | 22.7k |
| SubagentHandback | 6 | 12.9k |
| Agent | 9 | 4.3k |
| Read | 31 | 3.7k |
| Edit | 8 | 2.1k |
| Monitor | 2 | 935 |
| ToolSearch | 3 | 643 |
| (no tool) | 0 | 597 |
| Skill | 1 | 51 |
| **Total** | 212 | 98.2k |
