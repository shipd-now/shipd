# factory-doc-always-on
Status: verified
Planned-at: 983091e1681651d010d00d6c04bd1255bf5ac358
Gated-hash: 1b6ca6bf69d1

## Idea

Rewrite the `What it is for` section of `docs/shipd-factory.md` to lead with the always-on direction, and trim the page so it stays within its 100-line cap.

### Motivation

The repo owner asked that the page stress that the factory can stay on 24/7, works where the reader works, and takes its instructions through shipd. A repo owner deciding whether to install the App cannot learn that direction today, because the section describes only the host and one job.

### Details

- The section opens with one new paragraph: the factory works where you work, can stay on 24/7, and takes its settings through shipd.
- The paragraph names `.shipd-config.json` as today's lever, and skills added to the shipd harness as arriving once they ship.
- The paragraph says shipd is building a Slack connector and plans more for Teams and other tools. It gives the Slack app that reacts to Grafana errors as an example.
- Four trims pay for the six added lines; the page lands on exactly 100 lines.
- `docs/shipd-factory-setup.md` updates one link, because one heading on the concept page changes.

Affected capabilities: `shipd-factory-docs` (modified, requirement `shipd-factory-page`). Impact: `docs/shipd-factory.md`, `docs/shipd-factory-setup.md` line 150. No code, no plugin file, no version bump.

### Non-goals

- No connector, Slack app, or harness skill support. This change edits docs only.
- No change to the diagram, the permissions, the review, or the live-proof content.
- No new page, and no other edit to `docs/shipd-factory-setup.md` beyond the one link.
- No website change. The `docs-by-feature` epic owns the sidebar and leaves both factory pages in place.

## Implementation

- **The target page is fixed text.** `artefacts/shipd-factory.md` holds the whole page as it must read after the change. The executor applies it through `/s:document` and does not reword it. Rationale: the page sits on its cap, so any free rewording risks line 101.
- **Trim in place (Q1).** Four trims free the room:
  1. The mechanism paragraph drops "Google's ax agent runtime" and "Agent Substrate", and shrinks from four lines to three. The setup page still names and links both.
  2. The setup section drops the sentence about consent prompts.
  3. The `## Remove` section folds into the setup section as its last paragraph. The heading becomes `## Set up and remove`.
  4. The `New repo` proof bullet joins onto one line, like the two bullets above it.
  Rejected: moving a section to `docs/shipd-factory-setup.md`. That how-to page holds 150 lines, which is its cap. Rejected: a second concept page for the direction. The owner asked for the emphasis inside `What it is for`.
- **The setup page link follows the heading.** Line 150 of `docs/shipd-factory-setup.md` links `shipd-factory.md#set-up-a-repo`. It becomes `[Set up and remove](shipd-factory.md#set-up-and-remove)`. The line count stays 150.
- **Unshipped parts read as unshipped, in sentences (Q2, Q3).** The page says "shipd is building a Slack connector", "plans more for Teams and other tools", and "once they ship". It never uses the label `(planned)`, which the master scenario "Reviews and their access are stated" forbids.
- **Harness skills carry a qualifier.** `docs/customise.md:160-164` says a repo cannot override the steps a skill follows today. The page therefore names `.shipd-config.json` as today's lever and qualifies harness skills with "once they ship".
- **The spec gains two scenarios.** The delta restates every master scenario of `shipd-factory-page` and adds one for the always-on purpose and one for the planned connectors.

Risks:

- The page has no spare line. Any later edit must trim first. The lint scenario guards the cap.
- The term "shipd harness" also reads as the harness registry in `docs/customise.md`. The page uses the owner's phrase once and adds no definition.
- The connector sentences go stale when a connector ships. The scenario "Connectors read as not yet shipped" then fails review and forces the update.

## Questions and answers

### Q1: How does the new content fit under the 100-line cap?
- **Question:** `docs/shipd-factory.md` is a concept doc at 99 of 100 lines and gains an always-on paragraph. How does the new content fit? Options: (1) trim in place with the four trims listed under Implementation; (2) move a section to `docs/shipd-factory-setup.md`; (3) split the direction into a new concept page. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Trim in place, option 1. The setup page already sits on its 150-line cap, so option 2 needs cuts there too. Option 3 moves the emphasis out of the section the owner named.
- **Queued:** q-factory-doc-cap-fit

### Q2: How does the page word harness skills, which are in planning?
- **Question:** The page names skills added to the shipd harness as a way to tell the factory how to work. That ability is in planning, not shipped. Options: (1) name it with a "once they ship" qualifier, beside `.shipd-config.json` as today's lever; (2) state it as a present capability, and merge this change after harness skills ship; (3) leave harness skills out until they ship. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The sentence stays true before and after harness skills ship, and this change needs no ordering against that work.
- **Queued:** q-factory-doc-harness-skills-wording

### Q3: How does the page describe the connectors' status?
- **Question:** The request names connectors for Slack, Teams and other tools as future work, and a Slack intake may already exist privately. How does the page state their status? Options: (1) say none ships today and present all as planned; (2) say a Slack connector is in development and the others are planned.
- **Answered by:** USER
- **Answer:** Option 2. The page says shipd is building a Slack connector and plans more for Teams and other tools. It still never says a connector ships today.

## Readiness attestation

### Problem and motivation

The owner wants the page to stress the always-on, works-where-you-work direction. A repo owner reading the page today learns only the host and job mechanics.

Evidence:

- `docs/shipd-factory.md:11-16` holds the whole section: one paragraph on the host and one job.
- The owner's request names the section, 24/7 operation, connectors, and harness skills.
- Capability `shipd-factory-docs`, requirement `shipd-factory-page`, states the reader: a repo owner deciding whether to install the App.

### Scope and non-goals

The change edits two docs files and one requirement. It ships no connector, no skill support, and no website change.

Evidence:

- In scope: `docs/shipd-factory.md:11-16`, `:64-68`, `:92-99`; `docs/shipd-factory-setup.md:150`.
- Out of scope: `.shipd/epics/docs-by-feature/epic.md:41-43` leaves both factory pages in place and off the sidebar.
- `plugins/s/skills/document/references/standard.md` sets the caps with no exceptions: concept 100, how-to 150.

### Affected capabilities and files

One capability and two files are affected. The target text ran through the lint before emission and passed.

Evidence:

- Capability `shipd-factory-docs`: requirement `shipd-factory-page` (base 73d49113ad82, from `spec_status.py base-hash`).
- Files: `docs/shipd-factory.md` (99 lines today), `docs/shipd-factory-setup.md:150` (150 lines today).
- Runnable premise: `python3 -B plugins/s/skills/document/scripts/docs_lint.py` on a scratch copy of both target pages exited 0; `wc -l` printed 100 and 150.
- Runnable premise: `grep -c '(planned)'` on the target page printed 0, and the private-name grep from the master scenario printed nothing.
- Runnable premise: `python3 -B -m unittest discover -s plugins/s/skills/document/tests` ran 64 tests, OK.
- `.github/workflows/ci.yml:123-130` lints every file under `docs/` except `docs/retros/`.

### No open task-shaping decision

Three decisions shaped the tasks. The owner settled all three.

Evidence:

- How the content fits the cap (trim in place): owner's answer, Q1.
- How the page words harness skills (qualifier "once they ship"): owner's answer, Q2.
- Slack connector in development, others planned, none shipped: owner's answer, Q3.
- Routing through `/s:document`: settled by investigation, `AGENTS.md:132-137`.
