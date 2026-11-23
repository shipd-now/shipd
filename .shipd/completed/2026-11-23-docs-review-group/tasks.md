# Tasks — docs-review-group

Write every page through `/s:document` (load the `s:document` skill, or read
`plugins/s/skills/document/SKILL.md` and follow it). `plan.md`
§Implementation holds the binding shape, fact-owner, link, and rewrap rules.
Take facts only from the pages themselves and the sources that section names.

## 1. Reshape the semantic review pages

- [x] 1.1 [req: semantic-review-reference-doc] Edit
      `docs/semantic-review-reference.md`: insert a section
      `## The engine's subcommands` directly above `## The --json payload`
      (the heading that holds `--json` in backticks). Move into it the
      six-row subcommand table from the `## What it reads` section of
      `docs/semantic-review.md`, with one lead-in sentence. Rewrite the
      opening paragraph to call `semantic-review.md` the main page and to
      name the subcommands among what the page lists. Change nothing else.
      Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/semantic-review-reference.md`
      until it exits 0 at 250 lines or fewer.
- [x] 1.2 [req: semantic-review-doc] Rewrite `docs/semantic-review.md` into
      the main-page shape, keeping `<!-- doc-type: concept -->` on line 1
      and the title `# The semantic review`. Opening: keep the two existing
      paragraphs, and fold in from `## What it reads` only the sentence that
      `semdiff` does the mechanical work and emits compact JSON, and the
      line "The engine supplies the facts. The reviewer supplies the
      judgement." Delete the `## What it reads` heading and its table. Keep
      `## What it looks for` and `## Severity and the blocking rule` with
      every fact, including the words "Six triggers". Add
      `## When to use it`: run `/s:review` on local changes before a push;
      run it against a pull request to post findings; link
      `copilot-review.md` for a review on every pull request. Rename
      `## Where it runs` to `## How to run it`, name the `/s:review`
      invocation in its first sentence, and keep the mermaid fence and the
      paragraph below it. Demote `## When a tool is missing` to
      `### When a tool is missing` inside `## How to run it`. Replace
      `## See also` with `## Reference`, linking
      `semantic-review-reference.md` (the subcommands, the `--json` payload,
      the review event, the room-reviewer flags, the `lint` key, `prior`)
      and `copilot-review.md`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/semantic-review.md`
      until it exits 0 at 100 lines or fewer, then run
      `python3 -m unittest discover -s plugins/s/skills/review/tests -p test_skill_references.py`
      and confirm `OK`.

## 2. Reshape the review gate pages

- [x] 2.1 [req: copilot-review-guide, ci-usage-docs] Edit
      `docs/copilot-review-reference.md`. (a) Rewrap each paragraph and
      bullet that is hard-wrapped at 80 columns to 100 columns, changing no
      word. (b) Change the title to `# Review gate reference` and the
      opening link text to `[Review gate](copilot-review.md)`, calling it
      the main page. (c) Under `### The poll fallback mode`, add one bullet
      taken from the paragraph of `docs/copilot-review.md` that starts "One
      consequence lands on GitHub's review": on the poll surface the changed
      skill reviews the pull request that changes it; the CLI reviewer pins
      its instructions to the base ref. (d) Insert `## The spec lint action`
      directly above `## Scope and limits`, taking from `README.md` lines
      554-561 the `path` input (default `.`, the monorepo subdirectory example, the
      content directory resolved from `.shipd-config.json`) and the runner
      requirement (`python3` on the PATH; installs, downloads, and caches
      nothing). Keep every existing level-2 and level-3 heading text. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/copilot-review-reference.md`
      until it exits 0 at 250 lines or fewer.
- [x] 2.2 [req: copilot-review-guide, ci-usage-docs] Rewrite
      `docs/copilot-review.md` into the main-page shape, keeping
      `<!-- doc-type: how-to -->` on line 1. Title: `# Review gate`.
      Opening: the gate workflow turns the semantic review into the
      `semantic-review` commit status on every pull request; link `/s:review`
      to `semantic-review.md`; one sentence on the two reviewer modes,
      linking `copilot-review-reference.md`. Add `## When to use it`: install
      the gate to have every pull request reviewed before it merges; use
      `/s:review` alone for a review before a push; add the spec lint action
      to keep a malformed spec off `main`. Add `## How to run it` and place
      under it, as level-3 headings in this order: `### Before you start`
      (the current Prerequisites list and the `/s:gate` paragraph),
      `### 1. Install the files`, `### 2. Commit and push the files`,
      `### 3. Enable reviews`, `### 4. Set the reviewer token`,
      `### 5. Verify`, `### 6. Upgrade and uninstall`, and
      `### 7. Lint your specs in CI`. Steps 1 to 6 keep every fact they hold
      today, except that the paragraph starting "One consequence lands on
      GitHub's review" is deleted from step 2 (task 2.1 moved it). Step 7
      takes from `README.md` lines 524-552: what the action lints, the
      workflow snippet, and the pinned-ref advice, plus one sentence naming
      the `path` input's default `.` with a link to
      `copilot-review-reference.md#the-spec-lint-action`. Replace
      `## See also` with `## Reference`, linking
      `copilot-review-reference.md` (the reviewer modes, the verdict rules,
      the trust boundary, the limits, the report states, the lint action's
      inputs), `semantic-review.md`, and
      the research report at `.shipd/research/copilot-code-review/report.md` (linked from `docs/` with a leading `../`). Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/copilot-review.md`
      until it exits 0 at 150 lines or fewer.

## 3. Write the pull requests page

- [x] 3.1 [req: pr-user-docs] Create `docs/pr.md` with
      `<!-- doc-type: how-to -->` on line 1 and the title `# Pull requests`,
      covering every item the `pr-user-docs` requirement lists, in the
      main-page shape. Under `## How to run it` use the level-3 headings
      `### Write the pull request`, `### Merge it`, and
      `### Set the merge rules`. Sources: `plugins/s/skills/pr/SKILL.md`,
      `plugins/s/skills/build/SKILL.md` lines 640-720,
      `plugins/s/skills/gate/SKILL.md` lines 171-250,
      `plugins/s/bin/shipd gate rules --help`, and `docs/customise.md` lines
      62-65. Link `customise.md`, `semantic-review.md`, `copilot-review.md`,
      and `agent-identity.md`; write `/s:build` and `/s:autopilot` as inline
      code with no link. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/pr.md`
      until it exits 0 at 150 lines or fewer.

## 4. Verify the group

- [x] 4.1 [req: *] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/semantic-review.md docs/semantic-review-reference.md docs/copilot-review.md docs/copilot-review-reference.md docs/pr.md`
      and confirm exit 0. Run `wc -l` on the five files and confirm 100,
      250, 150, 250, and 150 lines or fewer, in that order. Confirm every
      relative link and every `#` anchor in the five files resolves. Run
      `grep -n "^## See also" docs/semantic-review.md docs/copilot-review.md docs/pr.md`
      and confirm no match. Run
      `grep -nE "spec_status\.py|review_gate\.py|merge_rules\.py" docs/pr.md`
      and confirm no match. Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests` and
      confirm `OK`. Run `git status --short` and confirm only those five
      files under `docs/` changed outside the content directory.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 212 | 101.8k |
| SubagentHandback | 10 | 18.4k |
| Write | 9 | 16.7k |
| Read | 30 | 4.1k |
| Agent | 9 | 4.1k |
| Edit | 5 | 1.9k |
| (no tool) | 0 | 931 |
| Skill | 4 | 478 |
| **Total** | 279 | 148.5k |
