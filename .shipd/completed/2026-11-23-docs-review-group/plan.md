# docs-review-group
Status: verified
Epic: docs-by-feature
Planned-at: 983091e1681651d010d00d6c04bd1255bf5ac358
Gated-hash: 3eed5390d727

## Idea

Give the Review and merge group one main page per feature: reshape the
semantic review and review gate pages, move the spec lint CI setup onto the
review gate page, and write the pull requests page.

### Motivation

A reader who wants to open or merge a pull request, or set the merge rules,
finds no docs page: `/s:pr` lives only in `README.md` and the cheatsheet. A
reader setting up CI must read the README for the spec lint action and a
differently shaped page for the review gate.

### Details

| file | title | type | cap |
| --- | --- | --- | --- |
| `docs/semantic-review.md` | The semantic review | concept | 100 |
| `docs/semantic-review-reference.md` | Semantic review reference | reference | 250 |
| `docs/copilot-review.md` | Review gate | how-to | 150 |
| `docs/copilot-review-reference.md` | Review gate reference | reference | 250 |
| `docs/pr.md` (new) | Pull requests | how-to | 150 |

Affected capabilities: `project-readme` (three modified requirements),
`ci-action` (one modified), `shipd-pr` (one added). Impact: five files under
`docs/`; no engine, skill, test, or CI change.

### Non-goals

- No edit to `README.md`, `AGENTS.md`, `docs/cheatsheet.md`, or another
  group's page. `docs-readme-slim` deletes the README "CI" section later.
- No file rename, so no inbound link fix; link text on another group's
  page stays with its owner.
- No change to the standard, `docs_lint.py`, the caps, or any skill, and
  no new nested reference page.

## Implementation

**Every page is written through `/s:document`**, ending with
`docs_lint.py <file>` at exit 0.

**The main-page shape (binding).** The three main pages close with
`## When to use it`, `## How to run it`, and `## Reference`, in that order, as
`docs-plan-group` fixed them. Run steps are
level-3 headings inside `## How to run it`. `semantic-review.md` keeps
`## What it looks for` and `## Severity and the blocking rule` before
`## When to use it`; they are part of "what it is". No page keeps a
`## See also` section.

**Fact owners (binding).** A non-owner gives one sentence and a link.

| fact | owner |
| --- | --- |
| Passes, severities, the blocking rule, both review paths, the missing tool | `semantic-review.md` |
| `semdiff` subcommands, payload, review event, flags, `lint` key, `prior` | `semantic-review-reference.md` |
| Gate install, enabling reviews, the token recipe, verify, upgrade | `copilot-review.md` |
| The spec lint workflow snippet and the pinned-ref advice | `copilot-review.md` |
| Reviewer modes, verdict, strictness, trust boundary, limits, report states | `copilot-review-reference.md` |
| The lint action's `path` input and runner requirement | `copilot-review-reference.md` |
| `/s:pr`, the ship commands, merge rules, `shipd gate rules` | `pr.md` |
| The `pr`, `pr-mode`, and `merge` keys | `customise.md` |
| The second-account rule | `agent-identity.md` |

**Decisions.**

- **The subcommand table moves to the nested reference (Q2).** The main page
  sits at its cap and must gain two sections. It keeps one sentence naming
  `semdiff`. Rejected: a how-to marker, which `semantic-review-doc` pins.
- **The token recipe stays on `copilot-review.md`.** `shipd doctor` and two
  skills cite that path.
- **The gate reference gains room by rewrap only.** It sits at 250 lines
  and gains about 15. Rewrap its 80-column paragraphs to 100 columns, the
  width its other paragraphs use, and reword nothing. Keep every level-2 and
  level-3 heading, so anchors hold.
- **`pr.md` owns merging (Q1).** It covers `/s:pr`, the push and auto-merge
  commands, the default required checks, and `shipd gate rules`.
- **The README keeps its "CI" section.** `ci-usage-docs` moves to the docs
  page; `docs-readme-slim` deletes the README copy.
- **Links.** Link only files on `main` plus this change's pages; write
  `/s:build` and `/s:autopilot` as inline code.
- **Diagrams.** `semantic-review.md` keeps its diagram; no page gains one.
- **Sources.** `pr.md` takes facts from `plugins/s/skills/pr/SKILL.md`,
  `plugins/s/skills/build/SKILL.md:640-720`,
  `plugins/s/skills/gate/SKILL.md:171-250`, `shipd gate rules --help`, and
  `docs/customise.md:62-65`. The lint action text comes from
  `README.md:524-561`.

Risk: `copilot-review.md` sits at 150 lines and gains three sections. Guard:
the changed-skill paragraph and the `path` detail go to the reference, and
the cap is a task exit condition.

## Questions and answers

### Q1: Main page for the merge rules verb
- **Question:** Which page is the main page for `shipd gate rules` and the
  merge rules? Options: (1) the pull requests page, in a merge-rules step;
  (2) the review gate page, beside `/s:gate`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The rules decide when a pull request merges, and the
  review gate page sits at its cap.
- **Queued:** q-docs-review-gate-rules-owner
- **Relied on by:** docs-room-group, docs-start-here

### Q2: Home of the semdiff subcommand table
- **Question:** Where does the six-row `semdiff` subcommand table on
  `docs/semantic-review.md` go? Options: (1) the nested reference page, with
  one sentence left on the main page; (2) it stays, and the page becomes a
  how-to with the 150-line cap; (3) it stays, and the remaining prose is
  compressed. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The table is lookup material, and the epic nests
  detail that exceeds a main page's cap.
- **Queued:** q-docs-review-semdiff-table-home

## Readiness attestation

### Problem and motivation

Pull requests and merge rules have no docs page, and CI setup is split
across the README and the gate page.

Evidence:

- `README.md:289` and `README.md:524-561`: the only prose on `/s:pr` and on
  the spec lint action.
- Epic Changes row `docs-review-group`.

### Scope and non-goals

Five docs files are in scope. The README, the cheatsheet, and other groups'
pages are out.

Evidence:

- Epic Design "The seams": `docs-readme-slim` owns README cuts and
  `docs-start-here` owns the cheatsheet.
- Epic Decision "A surviving page keeps its file name".

### Affected capabilities and files

Three capabilities and five files are affected: four modified docs
requirements, one added.

Evidence:

- `project-readme`: `semantic-review-doc` (base 06ddde91715b),
  `semantic-review-reference-doc` (base d4e63f83a4a0), `copilot-review-guide`
  (base d1c929c511b6). `ci-action`: `ci-usage-docs` (base 32f7039de88e).
  Hashes from `spec_status.py base-hash`. `shipd-pr`: no docs requirement.
- Files: `docs/semantic-review.md:1-100`,
  `docs/semantic-review-reference.md:1-171`, `docs/copilot-review.md:1-150`,
  `docs/copilot-review-reference.md:1-250`, and new `docs/pr.md`.
- Pins that still hold: `difft-required-docs`, `gate-skill-flow`,
  `doctor-remedy-boundaries`, `test_skill_references.py:916-935`.
- Runnable premise: `docs_lint.py` over the four existing pages → exit 0.
- Runnable premise: `python3 -m unittest discover -s
  plugins/s/skills/review/tests -p test_skill_references.py` → `OK`, 71 tests.
- Runnable premise: `plugins/s/bin/shipd gate rules` → exit 0, six members
  as `config` beside `live`; its `--help` lists `apply`, `--repo`, `--root`.
- Runnable premise: `plugins/s/bin/shipd copilot` → exit 0, four files
  `absent`. `shipd doctor` → printed a `merge-rules` line.

### No open task-shaping decision

Every task-shaping decision is settled: two by planner defaults, three by
earlier members' defaults.

Evidence:

- The merge rules' page and the subcommand table's home: planner defaults,
  Q1 and Q2.
- The file name `pr.md`, the new page's how-to type, and links to unmerged
  pages: `docs-plan-group` Q1, Q2, Q5; `docs-build-group` Q1, Q4, Q5;
  `docs-epics-group` Q1, Q3.
- Headings, fact owners, the README boundary, and diagrams: investigation,
  from the epic's Decisions and the sibling plans. The personal memory store
  is absent.
