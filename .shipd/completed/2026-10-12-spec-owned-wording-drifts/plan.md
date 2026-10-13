# spec-owned-wording-drifts
Status: verified
Theme: spec-engine

## Idea

### Motivation

Six requirements across three capabilities restate wording another requirement
owns, and in every case the owner has since moved. Four of the six demand a
state the live surface has already left, so the requirement demands a
regression.

- **`copilot-review-guide`** requires the reference doc to state the gate
  "classifies the output's last non-empty line" — the reader
  `gate-workflow-template` records as abandoned because the Copilot CLI
  streamed narration after the report and the rule fell open. It restates that
  classification a second time 16 lines later, and separately requires the doc
  to call `difft` "optional" with "engine degradation", which
  `difft-required-docs` forbids in both respects.
- **`semantic-review-doc`** requires the guide to name "the five risk-lens
  triggers" when `review-risk-lenses` defines six, and to say the review
  "degrades rather than stops when a tool is missing" when
  `difft-required-docs` requires it say the review stops.
- **`semantic-review-reference-doc`** requires "all ten `category` values" when
  both payload surfaces carry eleven.
- **`cheatsheet-doc`** names the README Skills groups "the core loop, bigger
  than one change, and knowledge" when
  `readme-catalogs-the-plugin-s-skills` requires **Pipeline**,
  **Orchestration** and **Memory**.
- **`epic-header-metadata`** validates `Theme:` against `.shipd/config.json`,
  which its own sibling `theme-vocabulary-config` forbids reading.
- **`workspaces-doc`** requires the teams page to state "the engine takes no
  locks and never pushes, pulls, or fetches", which
  `workspaces-doc-store-sync` forbids by name — in its prose *and* in its
  scenario.

### Details

Each stops restating and defers to the requirement that owns the subject.

### Non-goals

- **Two docs change; nothing else outside the spec library does.** For four of
  the six, the live surface already behaves the way its owning requirement
  says, so the edit moves a stale requirement onto the implementation. For the
  two **count** deferrals it is the other way round: strengthening them from
  "all five" and "all ten" to "every trigger the owner defines" and "every
  value the surfaces accept" leaves both requirements **unmet**, because
  `docs/semantic-review.md` says "Five triggers" and
  `docs/semantic-review-reference.md` says "one of the ten values below".
  A first attempt at this change asserted that no doc needed touching, shipped
  two unmet requirements, and the review blocked it with two `high`
  spec-coverage findings. The root cause was a verification gap, not a wrong
  deferral: the premise sweep checked the **owner** side of both counts and
  never the **doc the requirement governs**. Both docs are corrected here, and
  neither is under `plugins/`, so there is still no version bump and no
  measurement baseline movement.
- **No template change, and the only code touched is tests.** The guard that
  would have caught the unmet pair is added to
  `plugins/s/skills/review/tests/test_skill_references.py`, which forces a
  plugin version bump. Tests are not on the `/s:review` prompt path, so the
  bump moves no measurement baseline.
- **No change to any owning requirement.** All seven owners are already correct.
- **Three further sites are deliberately left**: `shipd-port`'s prohibition of
  the four constants its own preceding sentence mandates,
  `build-reporting`'s paragraph forbidding the `~/.shipd/` path it mandates
  eight lines earlier, and `shipd-plan`'s restatement of the rendered-body
  budget as 120 where `harness-command-bodies` owns it at 150. The first two
  share a mechanical cause — commit `1afdd19` rewrote source-side tokens
  *inside prohibition sentences*, turning "do not use the retired name" into
  "do not use the current name" — which deserves its own sweep rather than
  three hand-fixes.
- **No general lint guard.** A "no requirement restates another's wording"
  rule is not expressible as a lint check, and hard-coded phrase checks would
  rot the moment any owner reworded. What *is* pinned is narrower and exact:
  the two `docs/` pages must name every trigger and every `category` value,
  and must state no stale count. That is the gap that shipped two requirements
  unmet, and it is checkable.
- **Two further sites found by review and deliberately left.**
  `copilot-review-skill` mandates "a statement that the engine is read-only and
  degrades to its text engine when `difft` is unavailable", which `text-fallback`
  and `difft-required-docs` both forbid, and
  `plugins/s/integrations/copilot/SKILL.md` carries it — that fix needs a
  `plugins/` edit and a version bump. And
  `plugins/s/skills/review/references/risk-lenses.md` opens "Five triggers,
  four lenses" when the file has six sections and every other surface says six;
  that file is on the `/s:review` prompt path, and a ReviewBench measurement is
  queued against v0.6.279, so touching it now would move the baseline
  mid-cycle.
- No `plugins/s/` file changes, so no plugin version bump and no ReviewBench
  measurement baseline movement.

## Implementation

Six MODIFIED requirements. Each replaces the restated clause with a deferral
naming the owner and stating it SHALL NOT restate the wording, so the drift
cannot return by someone re-adding a copy.

**Prose and scenarios both.** A first attempt at this change fixed prose and
left scenarios, which made two requirements self-contradictory — deferring in
prose while demanding the forbidden claim in a scenario — and the semantic
review blocked it with two `high` findings. Every scenario that pins a
restated value is changed with its prose here: `copilot-review-guide`'s verdict
scenario, `semantic-review-doc`'s trigger scenario, and
`semantic-review-reference-doc`'s payload scenario. `workspaces-doc`'s
team-guide scenario carried the no-locks claim verbatim and is changed too.

**Where a deferral replaces a factual claim, it says what was wrong.**
`epic-header-metadata` names the retired path as the reason it will not name a
path; `workspaces-doc` names the no-locks claim as the thing its owner forbids;
`semantic-review-doc` and `semantic-review-reference-doc` each name the count
they previously fixed. A deferral that hides what it corrected invites the
correction being undone.

### Every deferral target was verified to exist and to own its subject

A deferral pointing at nothing is worse than the drift it replaces. Two of the
first drafts were wrong and were caught this way: `readme-skills-section` does
not exist — the owner is `readme-catalogs-the-plugin-s-skills` — and
`review-taxonomy-parity` owns *parity between the two payload surfaces*, not
the enumeration, so the category deferral names the surfaces as the source and
that requirement as what holds them in agreement.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.278 → 0.6.279, because the
docs guard lands in the review skill's test suite. Nothing on the `/s:review`
prompt path changes — no `SKILL.md`, no `references/`, no harness body — so a
ReviewBench measurement calibrated on v0.6.276's prompt is unaffected.

## Readiness attestation

### Problem and motivation

Six requirements contradict the requirement that owns their subject, and four
of them demand a state their live surface has already left.

Evidence, read in this worktree: `docs/copilot-review-reference.md` has no
"last non-empty" and describes the backwards scan at lines 51 and 95;
`difft-required-docs` says the reference doc "SHALL NOT list `difft` among
optional tools" and "SHALL carry no claim that a review degrades";
`docs/semantic-review.md` says the review "stops before any analysis" and still
says "Five triggers" while `SKILL.md` step 5b carries six;
`json-output.md` and `harness/references/review.md` both carry eleven category
values; `README.md` carries **Pipeline**, **Orchestration**, **Memory**;
`spec_common.CONFIG_FILENAME` is `.shipd-config.json` and no script under
`plugins/s/skills/build/scripts/` reads `.shipd/config.json`;
`docs/workspaces/teams.md` documents auto-commit under an exclusive lock and a
session-boundary hook that fetches, fast-forward merges and pushes.

### Scope and non-goals

In scope: six MODIFIED requirements across `project-readme`,
`shipd-spec-format` and `shipd-workspace`, including four scenario changes,
plus the two documentation files the strengthened count requirements govern.

Out of scope: every owning requirement, every file under `plugins/s/`, the
plugin version, the three self-contradiction sites, the two sites review found,
the namespace-port sweep, and any new lint guard.

### Affected capabilities and files

Three capabilities, six requirements, hashes from `spec_status.py base-hash`
here: `project-readme`'s `copilot-review-guide` (`c9499a95ed2e`),
`cheatsheet-doc` (`4c1a05aa27ff`), `semantic-review-doc` (`f77a9bdbfd67`) and
`semantic-review-reference-doc` (`eaf214c41d9a`); `shipd-spec-format`'s
`epic-header-metadata` (`3ce4f5065d18`); `shipd-workspace`'s `workspaces-doc`
(`c0491cb879f0`).

Files: the three master specs via their deltas, plus
`docs/semantic-review.md`, `docs/semantic-review-reference.md`,
`plugins/s/skills/review/tests/test_skill_references.py` and
`plugins/s/.claude-plugin/plugin.json`.

### No open task-shaping decision

- Which side changes in each case: the requirement, because every live surface
  already matches its owning requirement — settled above, with the grep
  evidence for each of the six.
- Transcribe the owner's wording or defer to it: defer, because a second copy
  is what produced all six, and this library already uses ownership-deferral
  for its two line ceilings and, since v0.6.277, for the copilot rubric and
  reader — settled above.
- Whether scenarios change with prose: yes, always, because the first attempt
  at this change proved that fixing one and not the other manufactures a
  self-contradiction — settled above, with the finding that caught it.
- How wide the change goes: the six in capabilities it already touches, with
  the remaining three and their shared mechanical cause named as a non-goal.
