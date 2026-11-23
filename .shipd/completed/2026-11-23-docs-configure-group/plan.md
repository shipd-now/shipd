# docs-configure-group
Status: verified
Epic: docs-by-feature
Planned-at: 983091e1681651d010d00d6c04bd1255bf5ac358
Gated-hash: a9fd38eddc7c

## Idea

Give the Configure group one main page per feature: reshape `customise.md`,
write the harnesses, statusline-and-telemetry, and doctor pages, and nest
`harness-agents-reference.md` under the harnesses page.

### Motivation

A reader who wants to add a harness, register the statusline, read the build
report, or repair a setup finds no docs page: those features live only in
`README.md` and the cheatsheet. The `docs-by-feature` epic assigns this
member the Configure group.

### Details

| file | title | type | cap |
| --- | --- | --- | --- |
| `docs/customise.md` | Customising shipd | reference | 250 |
| `docs/harnesses.md` (new) | Harnesses | how-to | 150 |
| `docs/harness-agents-reference.md` | Harness agents reference | reference | 250 |
| `docs/statusline-and-telemetry.md` (new) | Statusline and telemetry | how-to | 150 |
| `docs/doctor.md` (new) | Doctor | how-to | 150 |
| `docs/document.md` (new) | Write docs | how-to | 150 |

Affected capabilities: `shipd-config` and `harness-registry` (one modified
docs requirement each); `harness-registry`, `statusline`, and `shipd-doctor`
(one added docs requirement each); `shipd-document` (one added, Q3).
Impact: six files under `docs/`; no
plugin, engine, test, or CI change, so no version bump.

### Non-goals

- No edit to `README.md`, `AGENTS.md`, `docs/cheatsheet.md`,
  `docs/getting-started.md`, or another group's page. `docs-start-here` and
  `docs-readme-slim` own those, including the doctor check list on
  `getting-started.md` and the cheatsheet's `doctor --fix` section.
- No page for `shipd install`, `shipd update`, or `shipd vendor`; the install
  page in Start here owns them.
- No new nested reference page, no diagram, and no change to the standard,
  the caps, or any skill.

## Implementation

**Every page goes through `/s:document`** (epic Decision). Read
`plugins/s/skills/document/references/standard.md` first, put the marker on
line 1, and run `python3 plugins/s/skills/document/scripts/docs_lint.py
<file>` until it exits 0.

**Main-page shape (binding).** After the title, the opening paragraphs say
what the feature is. Then come `## When to use it`, `## How to run it`, and a
closing `## Reference`, with those exact headings. A page may add level-3
headings inside a section. No page keeps a `## See also` section.

**Doc types.** The four new pages are how-to, the default the Epics group
set (its Q1). `customise.md` stays `reference`: `customisation-guide` and
`test_config_sample.py` pin its marker and its key table.

**`customise.md` is reordered, not re-derived.** Its seven level-2 sections
become level-3 sections under `## Reference`, in today's order. The `shipd
config` commands move to `## How to run it`, which gains `/s:init` (Q2).
`## When to use it` is new. The links to the content directory's `README.md`
and `guardrails.md` stay in Reference prose; the other See-also links go.
Every backticked key stays in the table.

**Fact owners (binding).** A non-owner gives one sentence and a link.

| fact | owner |
| --- | --- |
| Config keys, layering, `shipd config`, `/s:init`, `shipd init` | `customise.md` |
| The registry, feature scaling, `shipd harness` verbs and flags, the ownership marker, the Aider file, the plugin-provided skip | `harnesses.md` |
| Agent file locations, frontmatter, role ids, adding a harness | `harness-agents-reference.md` |
| The statusline, the build report, its four settings and defaults, `shipd metrics` (Q1) | `statusline-and-telemetry.md` |
| `shipd doctor`, `--fix`, `/s:doctor`, the check list, the remedies | `doctor.md` |
| `/s:document`, the doc types, the caps, the diagram rule | `document.md` |
| Review gate setup, the Copilot token recipe | `copilot-review.md` |

So `customise.md`'s harness section shrinks to one sentence and a link.
`harness-agents-reference.md` opens with a link back to `harnesses.md`.

**Commands.** A page shows a `shipd` verb or a `/s:` skill, never an engine
script path. So the statusline page drops the README's `spec_status.py use`
command and its by-hand registration. The doctor page may also show a remedy
command.

**Links.** A page links only to files on `main` plus this change's own pages,
the default the Epics group set (its Q3). `/s:build`, `shipd board`,
`shipd install`, and `shipd worktree` appear as inline code.

**Sources.** State only behaviour confirmed in the source `tasks.md` names.

**Diagrams.** None. The registry, the doctor flow, and the report are lists.

Risk: the telemetry page holds three surfaces in 150 lines. Guard: cut what
the delta does not list.

## Questions and answers

### Q1: Main page for `shipd metrics`
- **Question:** Which docs page is the main page for the `shipd metrics`
  verb? Options: (1) the statusline-and-telemetry page, beside the build
  report; (2) the Build group's build page; (3) the cheatsheet alone.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The Build group's plan leaves `shipd metrics` and
  build telemetry to this group, and both report on finished deliveries.
- **Queued:** q-docs-configure-metrics-owner
- **Relied on by:** docs-start-here

### Q2: Main page for `/s:init` and `shipd init`
- **Question:** Which docs page is the main page for the `/s:init` wizard
  and the `shipd init` verb? Options: (1) `docs/customise.md`, since the
  wizard writes config keys; (2) the install page in Start here; (3) the
  getting-started walkthrough. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The wizard writes every answer through
  `shipd config set`, which `customise.md` already owns.
- **Queued:** q-docs-configure-init-owner
- **Relied on by:** docs-start-here

### Q3: Main page for `/s:document`
- **Question:** `/s:document` had no main page in any group. Options: (1)
  add a short how-to page in the Configure group; (2) a cheatsheet row only.
- **Answered by:** USER
- **Answer:** Option 1. This member adds `docs/document.md`, titled "Write
  docs", so every skill has one main page.
- **Relied on by:** docs-start-here

## Readiness attestation

### Problem and motivation

Harnesses, the statusline, build telemetry, and the doctor have no docs
page.

Evidence:

- Epic `docs-by-feature`, page map row "Configure" and Changes row
  `docs-configure-group`.
- `README.md:182-237`, `README.md:443-522`: the only long prose on harness
  mode, the statusline, and build telemetry.

### Scope and non-goals

Five files under `docs/` are in scope. The README, the cheatsheet, and
other groups' pages are out.

Evidence:

- Epic Design "The seams": `docs-start-here` owns the cheatsheet and
  getting-started, `docs-readme-slim` owns the README.
- Epic Decision "One page owns each fact": install lives on the install page.

### Affected capabilities and files

Five capabilities and six files are affected: two modified docs
requirements and three added ones.

Evidence:

- Modified: `shipd-config` `customisation-guide` (base f01242f214e5) and
  `harness-registry` `agent-surface-docs` (base a5bfc0c0d60c), hashes from
  `spec_status.py base-hash`.
- Added: `harness-registry`, `statusline`, `shipd-doctor`; none holds a
  `*-user-docs` id today.
- Files: `docs/customise.md:1-178`, `docs/harness-agents-reference.md:1-64`,
  and three new files.
- Runnable premise: `docs_lint.py docs/customise.md
  docs/harness-agents-reference.md` → exit 0.
- Runnable premise: `python3 -m unittest
  plugins/s/skills/build/tests/test_config_sample.py` → OK.
- Runnable premise: `plugins/s/bin/shipd harness --help` → exit 0, five
  verbs and five flags.
- Runnable premise: `shipd statusline --help` → exit 0, `install`, `layout`,
  five flags; bare `shipd statusline` → exit 0, report only.
- Runnable premise: `shipd metrics --help` → exit 0, four subverbs.
- Runnable premise: `shipd doctor` → exit 0, twenty check lines; its
  `--help` names `--fix`.
- Runnable premise: `shipd init status`, `shipd config check` → exit 0.

### No open task-shaping decision

Every task-shaping decision is settled; two rest on planner defaults here and
two on defaults an earlier member set.

Evidence:

- The owner of `shipd metrics` and of `/s:init`: planner defaults, Q1 and Q2.
- Doc type and link targets: the Epics group's planner defaults, its Q1 and
  Q3.
- File names: investigation; the short form and the title form agree.
- `customise.md` stays one reordered reference page: investigation, from the
  epic's fixed nested-reference list and the 250-line cap.
