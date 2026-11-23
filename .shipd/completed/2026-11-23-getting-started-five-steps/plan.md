# getting-started-five-steps
Status: verified
Planned-at: d93fff2f383fd537ed902e5a5342d40042a4cebb
Gated-hash: 52501d4d3a33

## Idea

Rewrite `docs/getting-started.md` as a short five-step guide, and give the
`/s:onboard` tour its own page.

### Motivation

The repository owner read "Your first change" on the website and found it
reads poorly: a newcomer cannot reach a first shipped change without wading
through a preflight step, a tour step, and installer detail. The website
will render this markdown directly, so the page itself must read well.

### Details

- `docs/getting-started.md` becomes five steps: 1 Install, 2 Plan your
  first change, 3 Build it, 4 Turn on the statusline, 5 Watch the board.
  `artefacts/getting-started.md` is the full page, 99 lines.
- The opening is two short paragraphs. No overview box, no command list.
- Install shows only the installer command and one collapsed
  `<details><summary>Alternative install</summary>` block. The block names
  the other modes in two sentences and links `install.md`, which owns them.
- The statusline is its own step, after the build and before the board. It
  says the statusline works in Claude Code only.
- The doctor step and the tour step leave the page, with no mention. The
  eco opt-in sentence leaves with the doctor step (Q2).
- `docs/onboard.md` is a new page, the main page for `/s:onboard` (Q1).
  `artefacts/onboard.md` is the full page, 73 lines.
- The `/s:onboard` row of `docs/cheatsheet.md` links `onboard.md`.

Affected capabilities: `project-readme` (four modified) and `shipd-onboard`
(one added). Impact: three files under `docs/`. Nothing under `plugins/s/`
changes, so the plugin version stays.

Hand-over to the `shipd-now-website` change (not built here):

- Its markdown renderer must render the HTML `<details>` and `<summary>`
  elements, with the markdown inside them, as a collapsed block.
- Its docs navigation gains the new page `docs/onboard.md`.

### Non-goals

- No edit to the website repository or its hand-built page.
- No edit to `docs/install.md`, `docs/doctor.md`, `docs/core-ideas.md`,
  `docs/what-is-shipd.md`, or the video scripts: none names a step of this
  page or links an anchor other than `#1-install`.
- No change to `docs_lint.py`, the documentation standard, or a test.
- No change to a requirement the `docs-findings-sweep` change modifies.

## Implementation

- **Both pages are written in advance.** The builder copies
  `artefacts/getting-started.md` over `docs/getting-started.md` and
  `artefacts/onboard.md` to `docs/onboard.md`, byte for byte, and writes no
  prose. Both artefacts pass `docs_lint.py`. Rejected: describing the page
  and letting the builder word it, because wording is judgement.
- **`<details>` needs no change to the lint or the standard.**
  `docs_lint.py` exits 0 on the artefact with the block in place. The
  standard (`plugins/s/skills/document/references/standard.md`) has no rule
  on inline HTML. A blank line sits after `<summary>` and before
  `</details>`, so GitHub renders the markdown inside.
- **The block points, it does not copy.** It names three modes (by hand
  with the Claude Code CLI, vendored into a repository, from a checkout)
  and links `install.md`. `docs/install.md` is not edited.
- **The statusline claim, as verified.** `shipd statusline install` writes
  a `statusLine` entry into Claude Code's user settings,
  `~/.claude/settings.json`. `plugins/s/integrations/statusline.sh` reads
  Claude Code session JSON on stdin. The harness registry
  (`plugins/s/skills/build/scripts/harness_registry.py:20`) declares four
  features and none is a statusline. So the page says: Claude Code only, no
  other harness has a statusline integration.
- **The newest-snapshot sentence stays, in plain words.** No other docs
  page states it, so it keeps its home here in one sentence.
- **`shipd status` and `shipd list` stay as one sentence** in step 5.
  `docs/plan.md` owns both verbs; a sentence costs two lines.
- **Step headings carry no command.** They read `## 2. Plan your first
  change`, not `## 2. Plan your first change: /s:plan`. `## 1. Install` is
  unchanged, so `docs/copilot-review.md:22` still resolves.
- **`customise.md` moves to "Where to go next".** `shipd-config`'s customise
  guide requirement needs the link on this page, so that requirement stays
  unmodified.
- **`shipd-install`'s `install-mode-docs` is not modified.** The new install
  step still meets its getting-started clause. `docs-findings-sweep`
  modifies that requirement, so leaving it alone avoids a rebase.
- **`/s:onboard` gets `docs/onboard.md` (Q1).** It follows the main-page
  shape and takes its facts from `shipd-onboard`'s verified requirements.

Risk: `docs-findings-sweep` merges first and edits `docs/cheatsheet.md`. It
changes the `harness` row only; this change edits the `/s:onboard` row. The
task gives the exact old text, and a builder that finds no match stops.

Follow-up outside this change: the wiki page `docs-main-page-shape` still
names a six-step guide that owns `/s:onboard`. `/s:teach` corrects it after
the merge.

## Questions and answers

### Q1: Which page owns /s:onboard once the guide drops it?
- **Question:** The guide was the main page for `/s:onboard`, and the
  cheatsheet row links it. Options: (1) a short how-to page
  `docs/onboard.md`; (2) the cheatsheet row alone, with no link; (3) keep
  the row linking a guide that no longer names the tour. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. Every skill has one main page; a skill no group
  owns gets a short how-to page rather than a cheatsheet row alone. The
  file name follows the skill.
- **Cited:** [[docs-main-page-shape]]

### Q2: Does the shorter guide keep the eco opt-in sentence?
- **Question:** The doctor step carried the one-line eco preset opt-in and
  the `customise.md` link. Options: (1) drop the sentence and keep one
  `customise.md` link under "Where to go next"; (2) keep the sentence in
  another step; (3) drop both. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. This is the planner's recommended default; no
  person typed it. No person was available, and the owner's standing
  instruction for this run was to adopt the recommended default on an
  insufficient verdict. The queue entry stays pending for the owner.
- **Queued:** q-first-change-guide-eco-mention

### Q3: What shape does the page take?
- **Question:** How should the first-change guide be laid out? Options: the
  owner's brief for this change. No oracle lookup ran, because the owner
  had already decided.
- **Answered by:** USER
- **Answer:** Seven decisions from the owner's brief. (1) No overview box
  or command list on top; a short opening, then the steps. (2) Install
  shows only the installer command and a collapsed "Alternative install"
  block; no installer output, no doctor paragraph. (3) Step 2 is `/s:plan`.
  (4) The statusline is its own step, after the build and before the board.
  (5) That step says the statusline works in Claude Code only. (6) The
  doctor step and the tour step leave the page, with no mention. (7) The
  website renders this markdown; its hand-built page is retired.

## Readiness attestation

### Problem and motivation

The owner read the guide on the website and found it reads poorly; a
newcomer meets two steps a first change does not need.

Evidence:

- `docs/getting-started.md:25-51` holds the doctor and tour steps.
- `docs/getting-started.md:111-123` buries the statusline in the watch step.
- Requirement `getting-started-doc` pins the six-step order.

### Scope and non-goals

Three docs files and five requirements; the website, the install page, the
linter, and the standard stay untouched.

Evidence:

- In scope: `docs/getting-started.md`, `docs/onboard.md`,
  `docs/cheatsheet.md:74`.
- Out of scope: `docs/install.md` (150 lines after `docs-findings-sweep`),
  `plugins/s/skills/document/scripts/docs_lint.py`.
- `shipd-install` requirement `install-mode-docs` and `shipd-config`'s
  customise guide requirement hold unmodified against the new page.

### Affected capabilities and files

Two capabilities and three files are affected, because the tour needs a new
owner page once the guide drops it.

Evidence:

- `project-readme`: `pipeline-follower-docs` (base 188efda95746),
  `getting-started-doc` (base 9c84cede3f35), `first-change-guide-owners`
  (base f925844b6fb6), `cheatsheet-page-links` (base 99aef8855bd5). Hashes
  from `spec_status.py base-hash`.
- `shipd-onboard`: added `onboard-user-docs`.
- No test reads the page: a search of `plugins/s/skills/*/tests` and
  `tools` for `getting-started` matches only the workspaces guide.
- Runnable premise: `docs_lint.py` on both artefacts → exit 0, 99 and 73
  lines, no finding on the `<details>` block.
- Runnable premise: `plugins/s/bin/shipd statusline --help` → "Report or
  register the shipd statusline in Claude Code's user settings".
- Runnable premise: `plugins/s/bin/shipd --help` → lists `board`, `status`,
  `list`, and `statusline [install|layout]`.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- The page shape, seven decisions: settled by the user, Q3.
- The owner page of `/s:onboard`: settled by the oracle, Q1.
- The eco sentence: recommended default adopted under the user's standing
  instruction, Q2.
- `<details>` passing the lint, the statusline scope, the fate of `shipd
  status` and `shipd list`, the heading text, and the home of the
  `customise.md` link: settled by investigation.
