# Tasks — docs-room-group

Write every page through `/s:document` (load the `s:document` skill, or read
`plugins/s/skills/document/SKILL.md` and follow it). `plan.md`
§Implementation holds the binding shape, fact-owner, link, rewrap, and
cut-order rules. Take facts only from the seven room pages and the two
`--help` outputs that section names. A moved fact keeps its wording. Run the
tasks in order: tasks 2.1 to 2.3 read text that task 3.1 rewrites and task
3.2 deletes.

`LINT` below means `python3 plugins/s/skills/document/scripts/docs_lint.py`.

## 1. Point the test at the merged page

- [x] 1.1 [req: room-skill-body] In
      `plugins/s/skills/room/tests/test_room_skill.py` line 31, change
      `"pr-room.md"` to `"room-run.md"` in `DOC_PATH`. Change nothing else.
      Run
      `python3 -m unittest discover -s plugins/s/skills/room/tests -p test_room_skill.py`
      and observe `test_reference_and_doc_use_the_540_timeout` fail: the
      current `docs/room-run.md` holds no `--timeout 540`.
- [x] 1.2 [req: room-run-tests-docs] Run
      `git show origin/main:plugins/s/.claude-plugin/plugin.json` and read
      its `version`. Set `version` in `plugins/s/.claude-plugin/plugin.json`
      to that value with the patch number raised by one.

## 2. Reshape the pages that receive moved text

- [x] 2.1 [req: room-reference-doc] Rewrite `docs/room-wake-reference.md`,
      keeping `<!-- doc-type: reference -->` on line 1. Title:
      `# Room reference`. Opening: the page lists the `shipd room` verbs and
      the Actions wake; link `room-run.md` as the how-to and
      `multi-agent-pr.md` as the model; keep the current sentence that links
      `copilot-review-reference.md`. Add `## When to use it`: install the
      wake so a CI agent answers addressed tasks with no session; use a local
      `shipd room run` for two agents that answer each other. Add
      `## How to run it`: the current `## Verbs` code block, then the
      `gh variable set SHIPD_ROOM_AGENT --body <name>` command and the
      `COPILOT_GITHUB_TOKEN` secret sentence from `## Configuration`. Add
      `## Reference` with these level-3 sections in this order:
      `### The room verbs` (a seven-row table from
      `plugins/s/bin/shipd room --help`, then the facts of
      `docs/pr-room.md` lines 11-13 and 42-45);
      `### How a turn ends` (`docs/pr-room.md` lines 106-120);
      `### Run flags` (the table at `docs/room-run.md` lines 105-115);
      `### The result line` (`docs/room-run.md` lines 119-137);
      `### The CI reviewer's review` (`docs/room-run.md` lines 70-85);
      `### What a turn may do` (`docs/room-run.md` lines 141-143 and
      `docs/pr-room.md` lines 130-142);
      `### When a run stalls` (`docs/multi-agent-autonomous-prs.md` lines
      114-121); then the current sections as `### The managed files`,
      `### The wake verbs` (the two paragraphs under the current `## Verbs`
      code block), `### Report states`, `### Configuration` (the table and
      the `author_association` paragraph), `### How a wake runs`,
      `### The reply marker`, and `### Known limits`, each with every fact it
      holds today. In `### Known limits`, link text for `room-run.md`
      becomes "Run agents in a pull request's room". Run
      `LINT docs/room-wake-reference.md` until it exits 0 at 250 lines or
      fewer.
- [x] 2.2 [req: agent-identity-docs-version] Rewrite
      `docs/agent-identity.md` into the main-page shape, keeping
      `<!-- doc-type: how-to -->` on line 1 and the title. Opening: keep the
      two current paragraphs; the `pr-room.md` link becomes
      `[Run agents in a pull request's room](room-run.md)`. Add
      `## When to use it`: before a reviewer agent approves; before a
      `shipd room run` with role `reviewer` or `ci`; then the three sentences
      at `docs/room-run.md` lines 44-46. Add `## How to run it` and place
      under it, as level-3 headings in this order: `### Before you start`
      (the current list, plus one sentence that a reviewer account that
      claims reviews needs push permission, linking
      `room-review-claims.md`), `### 1. Set up the second account`,
      `### 2. Start the reviewer session`, `### 3. Verify the account`,
      `### Verify an author bot`, and
      `### Keep the token out of the repository`, each with every fact it
      holds today. Replace `## See also` with `## Reference`, linking
      `room-run.md`, `multi-agent-pr.md`, and `semantic-review.md`. Run
      `LINT docs/agent-identity.md` until it exits 0 at 150 lines or fewer.
- [x] 2.3 [req: room-review-claims-doc] Edit `docs/room-review-claims.md`,
      keeping `<!-- doc-type: concept -->` on line 1 and the title. (a)
      Rewrap each paragraph and bullet that is hard-wrapped at 80 columns to
      100 columns, changing no word. (b) Keep
      `## How a runner claims a head`, `## The heartbeat`, `## Takeover`, and
      `## The poster fence` as they are. (c) Add `## When to use it` after
      `## The poster fence`: every `reviewer` and `ci` run claims a head with
      no setup; require the status when merges must wait for the claimed
      review. (d) Add `## How to run it`; rename `## The merge status` to
      `### Require the review status` and `## Permission` to
      `### Give the reviewer push permission`, and place both under it. (e)
      Add `## Reference`; demote `## Cleanup` and `## Limits` to level 3
      under it; replace `## See also` with one closing sentence that links
      `room-run.md` (the runner), `agent-identity.md` (the reviewer's
      account), and `semantic-review-reference.md` (the poster's flags). Run
      `LINT docs/room-review-claims.md` until it exits 0 at 100 lines or
      fewer.

## 3. Merge the three how-tos

- [x] 3.1 [req: multi-agent-walkthrough-doc, room-skill-body] Rewrite
      `docs/room-run.md` as the merged how-to, keeping
      `<!-- doc-type: how-to -->` on line 1. Title:
      `# Run agents in a pull request's room`. Write the opening,
      `## When to use it`, the seven level-3 headings under
      `## How to run it`, and `## Reference` exactly as the
      `multi-agent-walkthrough-doc` requirement lists them. Sources per
      step: `### Before you start` from `docs/pr-room.md` lines 15-23,
      `docs/room-run.md` lines 15-21, and
      `docs/multi-agent-autonomous-prs.md` lines 26-33;
      `### 1. Take one turn in a session` from `docs/pr-room.md` lines 25-32
      and 82-93; `### 2. Take a turn by hand` from `docs/pr-room.md` lines
      34-80 and 95-102, with the six commands in one fenced block;
      `### 3. Start the reviewer listener` from `docs/room-run.md` lines
      35-52 and 87-101; `### 4. Start the author listener` from
      `docs/room-run.md` lines 23-33 and 54-66, and one sentence on the "Fix
      required" turn that links `room-wake-reference.md`;
      `### 5. Watch the flow` from `docs/multi-agent-autonomous-prs.md` lines
      13-22 and 72-94; `### 6. Merge from a clear room` from
      `docs/pr-room.md` lines 122-126 and one sentence from
      `docs/multi-agent-autonomous-prs.md` lines 96-101 that links
      `room-review-claims.md`. Wrap prose at 100 columns. Include every
      string the plan's pinned-strings decision lists. Leave out the flag
      table, the result line, and the account refusal rule. Run
      `LINT docs/room-run.md` until it exits 0 at 150 lines or fewer; when
      over, apply the plan's cut order. Run
      `python3 -m unittest discover -s plugins/s/skills/room/tests` and
      confirm `OK`.
- [x] 3.2 [req: multi-agent-walkthrough-doc] Run
      `git rm docs/pr-room.md docs/multi-agent-autonomous-prs.md`.
- [x] 3.3 [req: room-skill-docs] Rewrite `docs/multi-agent-pr.md` into the
      main-page shape, keeping `<!-- doc-type: concept -->` on line 1, the
      title, and the mermaid fence unchanged. Rewrap 80-column paragraphs to
      100 columns. Keep `## Why a room`, `## The model`, and
      `## Who acts when` with every fact. Move
      `## The review gate is the first member` to directly after
      `## Who acts when`. Add `## When to use it`: a pull request needs a
      room when more than one agent, or an agent and a person, take turns on
      it. Rename `## Two ways a turn runs` to `## How to run it`; keep its
      two bullets and the addressed-task paragraph, add a third bullet for
      `shipd room run` on a developer machine, and link
      `[Run agents in a pull request's room](room-run.md)`. Replace
      `## See also` with `## Reference`, linking `room-run.md`,
      `room-wake-reference.md` (titled "Room reference"),
      `room-review-claims.md`, `agent-identity.md`, `customise.md`, and
      `semantic-review.md`. Run `LINT docs/multi-agent-pr.md` until it exits
      0 at 100 lines or fewer.

## 4. Verify the group

- [x] 4.1 [req: *] Run
      `LINT docs/room-run.md docs/room-wake-reference.md docs/agent-identity.md docs/multi-agent-pr.md docs/room-review-claims.md`
      and confirm exit 0. Run `wc -l` on the five files and confirm 150,
      250, 150, 100, and 100 lines or fewer, in that order. Confirm every
      relative link in the five files resolves. Run
      `grep -rnE "pr-room\.md|multi-agent-autonomous-prs" docs README.md AGENTS.md plugins tools --exclude-dir=retros`
      and confirm no match. Run `grep -n "^## See also"` over the five files
      and confirm no match. Run
      `grep -rn "exits .1. with one" docs/room-run.md docs/multi-agent-pr.md`
      and confirm no line states the account refusal. Compare each
      `shipd room run` flag in `docs/room-run.md` and
      `docs/room-wake-reference.md` with
      `plugins/s/bin/shipd room run --help`. Run
      `python3 -m unittest discover -s plugins/s/skills/room/tests` and
      `python3 -m unittest discover -s plugins/s/skills/review/tests` and
      confirm `OK` for each. Run `git status --short` and confirm the only
      changes outside the content directory are the five pages, the two
      deletions, `test_room_skill.py`, and `plugin.json`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 122 | 85.8k |
| Write | 7 | 22.4k |
| SubagentHandback | 3 | 6.2k |
| Read | 20 | 4.3k |
| Agent | 5 | 2.2k |
| (no tool) | 0 | 694 |
| **Total** | 157 | 121.7k |
