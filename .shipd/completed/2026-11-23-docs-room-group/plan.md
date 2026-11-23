# docs-room-group
Status: verified
Epic: docs-by-feature
Planned-at: 983091e1681651d010d00d6c04bd1255bf5ac358
Gated-hash: 278d87d9c237

## Idea

Merge the three room how-tos into one, make `agent-identity.md` the owner of
the second-account rule, and reshape the room concept, wake, and claims pages.

### Motivation

A reader who wants to run agents on a pull request must read three how-tos
that walk the same flow, and cannot tell which one to follow. The
second-account rule is also stated on three pages, so no page is the one to
trust.

### Details

| file | title | type | cap | action |
| --- | --- | --- | --- | --- |
| `docs/room-run.md` | Run agents in a pull request's room | how-to | 150 | the merged how-to |
| `docs/pr-room.md` | | | | deleted |
| `docs/multi-agent-autonomous-prs.md` | | | | deleted |
| `docs/room-wake-reference.md` | Room reference | reference | 250 | reshaped, gains the lookup detail |
| `docs/agent-identity.md` | Give an agent its own GitHub account | how-to | 150 | reshaped, owns the rule |
| `docs/multi-agent-pr.md` | Multi-agent PR | concept | 100 | reshaped |
| `docs/room-review-claims.md` | Review claims | concept | 100 | reshaped |

Affected capabilities: `shipd-room` (three modified requirements, one
added), `room-runner` (one modified, one added), `room-acting-account` (one
modified). Impact: seven files under `docs/`, one path constant in
`plugins/s/skills/room/tests/test_room_skill.py`, and the plugin version.

### Non-goals

- No edit to `README.md`, `AGENTS.md`, `docs/cheatsheet.md`,
  `docs/team-merge-test.md`, `docs/retros/`, or another group's page.
- No change to the standard, `docs_lint.py`, the caps, any skill, or any
  `shipd room` behaviour.
- No new page and no fifth nested reference page.
- No redirect for the two deleted pages.

## Implementation

**Every page is written through `/s:document`**, ending with
`docs_lint.py <file>` at exit 0.

**The main-page shape (binding).** Every page closes with `## When to use it`,
`## How to run it`, and `## Reference`, in that order, as `docs-plan-group`
fixed them. Run steps are level-3 headings inside `## How to run it`. The two
concept pages keep their explaining sections before `## When to use it`; they
are part of "what it is". No page keeps a `## See also` section.

**Fact owners (binding).** A non-owner gives one sentence and a link.

| fact | owner |
| --- | --- |
| Cards, Messages, the six states, who acts when, the round cap, the gate as first member | `multi-agent-pr.md` |
| `/s:room`, `stay`, the by-hand turn, both listeners, the first review and re-review tasks, repo mode, the #40 walk, merging from a clear room | `room-run.md` |
| The verb table, the `run` flags, the result line, how a turn ends, the CI reviewer's review, what a turn may do, stalls | `room-wake-reference.md` |
| The Actions wake: managed files, verbs, report states, settings, jobs, reply marker, limits | `room-wake-reference.md` |
| The second-account rule: an own approval never counts, the reviewer and `ci` refusal on the author's account, credentials, `whoami` | `agent-identity.md` |
| Claims, heartbeat, takeover, the poster fence, the `room-review/<agent>` status, push permission, the `0.6.345` floor | `room-review-claims.md` |
| The `room` key | `customise.md` |
| Review gate setup | `copilot-review.md` |
| Merge rules and `shipd gate rules` | the pull requests page (`docs-review-group` Q1) |

**Decisions.**

- **The merged page is `room-run.md` (Q1).** Five verified requirements and
  one test already read that path, so it needs the fewest rewrites. Rejected:
  `pr-room.md`, which forces edits in `semantic-review`.
- **The lookup detail moves to `room-wake-reference.md` (Q2).** The three
  how-tos hold 433 lines and the merged page gets 150. The reference sits at
  115 of 250 lines. It is retitled `# Room reference` and keeps its path.
  Rejected: a new `room-reference.md`, which the epic's list of four nested
  pages does not name. Rejected: cutting the flag table and the result line.
- **Other requirements pin strings on `room-run.md`.** The merged page keeps
  `--timeout 540`, `GH_CONFIG_DIR=~/.config/gh-reviewer`, `--request-review`,
  `--skill review-finding`, `re-review`, `claude auth login`,
  `shipd room run --repo`, `--state`, `Ctrl-C`, `/s:review`,
  `semantic-review`, and `copilot-review-gate.yml`.
- **Cut order for the merged page.** When it runs over 150 lines, move
  repo-mode detail beyond `--repo`, `--state`, and `Ctrl-C` to the reference
  first, then by-hand prose beyond the two timeouts and the cursor.
- **Concept pages gain room by rewrap only.** `room-review-claims.md` sits at
  its cap. Rewrap its 80-column paragraphs to 100 columns and reword nothing;
  that frees 8 lines for the 6 the shape adds. `docs-review-group` set this
  precedent.
- **`agent-identity.md` keeps its title.** `team-merge-test.md` cites it by
  that title and is out of scope.
- **Links.** Link only files on `main` plus this change's pages (the Plan,
  Build, and Epics groups' default). `shipd gate rules apply` appears as
  inline code with no link, because the pull requests page is unmerged.
- **Diagrams.** `multi-agent-pr.md` keeps its state diagram, which
  `room-skill-docs` pins. No page gains one: the #40 walk is a numbered list.
- **Sources.** The seven pages themselves, `plugins/s/bin/shipd room --help`,
  and `plugins/s/bin/shipd room run --help`. A moved fact keeps its wording.
- **Version.** The test edit touches `plugins/s/`, so `AGENTS.md` requires a
  patch bump of `plugins/s/.claude-plugin/plugin.json`.

Risk: the merged page is tight at 150 lines. Guard: the cut order above, and
the cap is a task exit condition. Risk: a deleted page keeps an inbound link.
Guard: a grep for both file names is a verify step.

## Questions and answers

### Q1: File name of the merged room how-to
- **Question:** Which file name does the one merged room how-to keep?
  Options: (1) `room-run.md`; (2) `pr-room.md`; (3)
  `multi-agent-autonomous-prs.md`; (4) a new name such as `room.md`.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. Five verified requirements and a test already pin
  that path, and the name fits a how-to about running agents.
- **Queued:** q-docs-room-merged-howto-filename
- **Relied on by:** docs-start-here, docs-readme-slim

### Q2: Home of the lookup detail the merged how-to cannot hold
- **Question:** Where do the `shipd room run` flag table, the result line,
  the turn-ending rules, and the CI-reviewer rules go? Options: (1)
  `docs/room-wake-reference.md`, retitled "Room reference", gains the
  sections; (2) a new nested `docs/room-reference.md`; (3) cut the detail.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The epic names no fifth nested reference page and
  rejects cutting flag tables, and the page has 135 free lines.
- **Queued:** q-docs-room-overflow-reference-home

## Readiness attestation

### Problem and motivation

Three how-tos walk the same room flow, and three pages state the
second-account rule.

Evidence:

- `docs/pr-room.md:1-150`, `docs/room-run.md:1-150`, and
  `docs/multi-agent-autonomous-prs.md:1-133` each show the listener or turn
  commands.
- The rule appears at `docs/agent-identity.md:5-8`, `docs/room-run.md:44-46`,
  and `docs/multi-agent-autonomous-prs.md:30-32`.
- Epic Changes row `docs-room-group` and Decision "Merge only where text
  repeats".

### Scope and non-goals

Seven docs files, one test constant, and the plugin version are in scope.
The README, the cheatsheet, and other groups' pages are out.

Evidence:

- Epic Design "The seams": `docs-readme-slim` owns README cuts and
  `docs-start-here` owns the cheatsheet.
- Epic Non-goals: `team-merge-test.md` and `docs/retros/` stay in place.
- A grep of `README.md`, `AGENTS.md`, `plugins/`, and `tools/` finds the two
  deleted names only at `test_room_skill.py:31`.

### Affected capabilities and files

Three capabilities and nine files are affected: five modified requirements
and two added.

Evidence:

- `shipd-room`: `room-skill-body` (base 3cc7dfa1bd0d), `room-skill-docs`
  (base aa03643323bf), `multi-agent-walkthrough-doc` (base 9efd2ec3d3cc).
  `room-runner`: `room-run-tests-docs` (base 143d91020f9d).
  `room-acting-account`: `agent-identity-docs-version` (base ee81084670ab).
  Hashes from `spec_status.py base-hash`.
- Pins that still hold unedited: `room-run-handoff-docs`,
  `room-run-repo-docs`, `room-skill-reviewer-review`,
  `review-branding-ships`, `copilot-room-wake-self-contained`,
  `multi-agent-pr-entry-links`.
- Files: the seven pages in Details,
  `plugins/s/skills/room/tests/test_room_skill.py:31`, and
  `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `docs_lint.py` over the seven existing pages → exit 0.
- Runnable premise: `python3 -m unittest discover -s
  plugins/s/skills/room/tests` → `OK`, 411 tests.
- Runnable premise: `plugins/s/bin/shipd room --help` → exit 0, seven verbs:
  `join`, `list`, `whoami`, `message`, `close`, `watch`, `run`.
- Runnable premise: `plugins/s/bin/shipd room run --help` → exit 0, listing
  `--max-turns`, `--budget`, `--state`, `--harness`, `--model`,
  `--turn-timeout`, `--interval`, `--request-review`, and `--ci-reviewer`.

### No open task-shaping decision

Every task-shaping decision is settled: two by planner defaults, two by
earlier members' defaults.

Evidence:

- The merged page's file name and the home of the lookup detail: planner
  defaults, Q1 and Q2.
- Links to unmerged pages: `docs-plan-group` Q5, `docs-build-group` Q5,
  `docs-epics-group` Q3. The merge rules' owner: `docs-review-group` Q1.
- Headings, fact owners, the rewrap, the kept title, and diagrams:
  investigation, from the epic's Decisions and the sibling plans. The
  personal memory store is absent.
