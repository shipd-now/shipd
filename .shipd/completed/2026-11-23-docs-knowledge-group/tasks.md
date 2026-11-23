# Tasks — docs-knowledge-group

Write every page through `/s:document` (load the `s:document` skill, or read
`plugins/s/skills/document/SKILL.md` and follow it). `plan.md`
§Implementation holds the binding type, cap, shape, fact-owner, command, and
link rules. Take facts only from the source files that section names.

## 1. Write the new pages

- [x] 1.1 [req: wiki-user-docs] Create `docs/wiki.md` with
      `<!-- doc-type: how-to -->` on line 1 and the title `# The wiki`,
      covering every item the `wiki-user-docs` requirement lists, in the
      main-page shape. Under `## How to run it` use the level-3 headings
      `### Teach the wiki`, `### Correct an answer`, and
      `### Promote to a base store`. In `## Reference`, add the store table
      and the verb table. Sources: `plugins/s/skills/teach/SKILL.md`,
      `plugins/s/agents/teacher.md`, and `plugins/s/bin/shipd --help`. Link
      `oracle.md`, `memory.md`, and `workspaces.md`; write `/s:plan`,
      `/s:build`, and `/s:init wiki` as inline code with no link. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/wiki.md`
      until it exits 0 at 150 lines or fewer.
- [x] 1.2 [req: memory-user-docs] Create `docs/memory.md` with
      `<!-- doc-type: how-to -->` on line 1 and the title
      `# Personal memory`, covering every item the `memory-user-docs`
      requirement lists, in the main-page shape. Under `## How to run it`
      use the level-3 headings `### Capture a preference`,
      `### List your memories`, and `### Forget a memory`. Sources:
      `plugins/s/skills/remember/SKILL.md`,
      `plugins/s/skills/memory/SKILL.md`, and
      `plugins/s/skills/forget/SKILL.md`. Link `oracle.md`, `wiki.md`, and
      `customise.md`; write `/s:plan` and `/s:init memory` as inline code
      with no link. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/memory.md`
      until it exits 0 at 150 lines or fewer.

## 2. Reshape the oracle page

- [x] 2.1 [req: oracle-user-docs] Rewrite `docs/oracle.md` into the
      main-page shape, keeping `<!-- doc-type: reference -->` on line 1.
      Keep every fact of the opening and of `## The ladder`, and keep its
      mermaid fence as it is. Add `## When to use it` after the ladder: run `/s:ask`
      when a decision is not in the codebase and before a person is
      interrupted; `/s:plan` consults the oracle by itself; never ask what
      reading the repository answers. Source:
      `plugins/s/skills/ask/SKILL.md`. Rename `## Using it directly` to
      `## How to run it` and move it directly after `## When to use it`. Add
      `## Reference` after it and move under it, one heading level down,
      `The two verdicts`, `The bar: definitive evidence, or nothing`,
      `What gets captured`, and `Correcting an answer`. In the opening,
      replace `spec_status.py oracle-lookup` with `oracle-lookup`.
- [x] 2.2 [req: oracle-user-docs] In `docs/oracle.md`, cut
      `### Correcting an answer` to three facts: the capture path writes an
      answer once; corrections go through `/s:teach`, with a link to
      `wiki.md` for the steps; a typed answer always supersedes the oracle.
      In `### What gets captured`, turn the sentence on `/s:remember` into
      one sentence linking `memory.md`. Delete `## See also`; put the links
      to `what-is-shipd.md` and `workspaces.md` into the opening prose and
      the `Queued: none` paragraph. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/oracle.md`
      until it exits 0 at 250 lines or fewer.

## 3. Verify the group

- [x] 3.1 [req: *] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/oracle.md docs/wiki.md docs/memory.md`
      and confirm exit 0. Confirm every relative link in the three files
      resolves to a file in the worktree, and that
      `docs/tutorials/videos/06-oracle-and-supersession-gate.md` still
      resolves its `oracle.md` link. Run
      `grep -nE "spec_(status|emit|gate)\.py" docs/oracle.md docs/wiki.md docs/memory.md`
      and confirm no match. Run
      `python3 -c "import re,sys; sys.exit(bool(re.search('[─-╿]', open('docs/oracle.md').read())))"`
      and confirm exit 0, meaning no box-drawing character.
      Run `git status --short` and confirm only those three files under
      `docs/` changed outside the content directory.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 96 | 46.5k |
| Write | 7 | 14.3k |
| SubagentHandback | 3 | 4.8k |
| Agent | 6 | 3.2k |
| Read | 7 | 1.0k |
| Edit | 2 | 648 |
| (no tool) | 0 | 301 |
| Skill | 1 | 77 |
| **Total** | 122 | 70.9k |
