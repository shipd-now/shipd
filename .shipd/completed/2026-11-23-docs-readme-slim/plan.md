# docs-readme-slim
Status: verified
Epic: docs-by-feature
Planned-at: a98bfe45750af18f0847f1c2d3a704da41b78132
Gated-hash: 6bf41182431d

## Idea

Cut `README.md` to the pitch, the install steps, one link per docs group, and
the contributor notes, and stop treating it as a list of every skill.

### Motivation

A reader who opens the repository must scan 619 lines to find where a feature
is explained, and each fact there also sits on a docs page, so the copies
drift. A maintainer who adds a skill must also edit a README table the cheatsheet
repeats.

### Details

- Replace README lines 13 to 562 with `artefacts/readme-middle.md`: a short
  `## Install` and nine group links. Keep the intro and contributor notes.
- Drop `README.md` from the skill registration surfaces: eight requirements
  and six tests.
- Point the `install.sh` header comment at `docs/install.md`.

Affected capabilities: `project-readme` (five modified, two removed, one
added), `shipd-install`, `shipd-document`, `shipd-drift`, `shipd-gate`,
`shipd-fix`, `shipd-doctor`, `shipd-init`, `shipd-pr`, and `shipd-room` (one
modified each). Impact: `README.md`, `install.sh`, six test files under
`plugins/s`, and `plugin.json` for the version bump.

### Non-goals

- No edit to any page under `docs/`, and none to `AGENTS.md`: nothing there
  links a README section.
- No backfill of README detail into docs pages (Q2).
- No change to a skill, an engine script, or the cheatsheet.

## Implementation

**The README text is fixed.** `artefacts/readme-middle.md` holds the new
`## Install` and `## Documentation` sections word for word. The executor
copies it and writes no prose.

**README shape.** Lines 1 to 12 (icon and intro) stay as they are, so
`readme-brand-marks`, `readme-displays-the-shipd-banner`, and
`readme-workspaces-flagship-link` hold unedited. Then `## Install`,
`## Documentation`, and the four contributor sections from `## Structure` to
the end (Q1). The result is about 130 lines; the cap is 150.

**Install stays lossless on the README.** It keeps the one-liner, the raw
URL, the two `claude plugin` commands, the launcher path, and `shipd doctor`.
`install.md` leaves the raw URL out, so the README is its only home.

**One link per group.** Each line links the group's opening page.
`customisation-guide` already requires the `docs/customise.md` link. The
closing sentence links the cheatsheet, the only list of every command (epic
Decision).

**Owners of the deleted sections.**

| README section | owner |
| --- | --- |
| Install mode detail, Per-repo mode, Dev mode, PATH | `docs/install.md` |
| Harness mode | `docs/harnesses.md` |
| Skills, The `shipd` CLI | `docs/cheatsheet.md` |
| The spec engine, Lifecycle | `docs/core-ideas.md`, `docs/plan.md`, `docs/customise.md` |
| Statusline, Build telemetry | `docs/statusline-and-telemetry.md` |
| CI | `docs/copilot-review.md` |

Detail the docs members left out goes with its section (Q2); `shipd-install`'s
`cache-launcher` requirement still records the launcher rules.

**Registration surfaces (Q3).** A skill is registered in `AGENTS.md` and
`docs/cheatsheet.md`. Eight requirements and six tests drop the README. The
tests live under `plugins/s`, so the plugin version rises by one patch.
`cheatsheet-doc` now owns the group names `Pipeline`, `Orchestration`, and
`Memory`; the cheatsheet file itself does not change.

**Rebase points.** Four deltas build on text an earlier member installed:
`pipeline-follower-docs`, `harness-mode-docs`, and `install-mode-docs`
(`docs-start-here`), and `room-skill-docs` (`docs-room-group`). Both members
have merged, and the four `base:` hashes name the master text they left. The
deltas carry no `Dropped:` line for "Doctor list matches the shipped checks"
or "Getting started carries the mode": master no longer holds either
scenario.

**Facts with no other home stay.** The build audit found three README facts
that no doc, spec, skill, or script states: the vendored launcher runs
directly, the in-session `/plugin` commands for a checkout, and the plugin as
the engine's distribution vehicle. The run's owner ruled that such a fact
stays. `## Structure` keeps the first and third; `## After editing` keeps
the second.

Risk: an owner page is missing at build time. Guard: task 1.1 checks every
owner file and a marker in each, and stops on a miss.

## Questions and answers

### Q1: Contributor sections of the README
- **Question:** No docs page owns Structure, Adding a command, Adding a
  skill, and After editing. Options: (1) keep them in `README.md` below the
  docs links; (2) delete them; (3) move them into `AGENTS.md`.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The epic deletes a README section only once a docs
  page owns it, and `readme-retains-onboarding-content` pins these.
- **Queued:** q-docs-readme-slim-contributor-sections

### Q2: README detail no docs page took
- **Question:** The docs members left out the launcher's version ordering,
  `SHIPD_PLUGIN_CACHE`, the wordmark note, `spec_status.py use`, and the CLI
  delegation notes. Options: (1) delete each with its section; (2) keep it in
  `README.md`; (3) backfill the owning docs pages. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The sibling plans left these out on purpose, and the
  verified specs and `--help` still record them.
- **Queued:** q-docs-readme-slim-unowned-detail

### Q3: README as a skill registration surface
- **Question:** Eight requirements and six tests require the README to name
  a skill. Options: (1) drop `README.md` from the registration surfaces and
  edit the requirements and tests; (2) name every skill in the README group
  lines so the tests pass unchanged. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The epic makes the cheatsheet the only list of every
  skill, and option 2 leaves the requirements naming a table that is gone.
- **Queued:** q-docs-readme-slim-registration-surfaces

## Readiness attestation

### Problem and motivation

The README repeats what the docs pages own, so the two copies drift.

Evidence:

- `README.md:13-562` against the owner table above.
- Epic `docs-by-feature`: fourth success criterion; Changes row
  `docs-readme-slim`.

### Scope and non-goals

The README, six tests, one comment, and the version are in scope. Every
`docs/` page and `AGENTS.md` are out.

Evidence:

- Epic Design "The seams" gives the README cuts to this member.
- A grep of `docs/`, `plugins/s`, `AGENTS.md`, `install.sh`, and `.github`
  for links to `README.md` sections finds only `install.sh:2`.
- Runnable premise: the six registration tests ran with `python3 -m
  unittest` and reported OK; `sh -n install.sh` exited 0.

### Affected capabilities and files

Ten capabilities and ten files are affected, because skill registration
requirements pin README content.

Evidence:

- `project-readme`: `readme-retains-onboarding-content` (980f7ae6d288),
  `pipeline-follower-docs` (73d6bb147c40), `harness-mode-docs`
  (0df33e2bf434), `cheatsheet-doc` (f4119d8ac7c1),
  `multi-agent-pr-entry-links` (a051efa446b6),
  `readme-catalogs-the-plugin-s-skills` (eb7d61754b21),
  `readme-documents-spec-engine` (1e2d8ca3e1a9).
- `install-mode-docs` (b3a1d06881e8), `document-registration`
  (6c548f2bbf21), `drift-skill-registration` (eb01487e09ac),
  `gate-skill-registration` (9d81d7a53128), `fix-skill-registration`
  (26725fe22574), `doctor-skill-registration` (895df18aaf14),
  `init-skill-sections` (374ffe175c31), `pr-callers` (7ae0ef723b90),
  `room-skill-docs` (70b8fd78ccfb). Hashes from `spec_status.py base-hash`.
- Tests under `plugins/s/skills`: `room/tests/test_room_skill.py:204`, `pr/tests/test_pr_skill.py:115`,
  and under `build/tests`: `test_init_skill_contract.py:58`,
  `test_drift_skill_contract.py:72`, `test_plan_deep_skill_contract.py:70`,
  `test_autopilot_skill_contract.py:132`.
- Files: `README.md:13-562`, `README.md:593`, `install.sh:2`,
  `plugins/s/.claude-plugin/plugin.json`.

### No open task-shaping decision

Every task-shaping decision is settled; three rest on planner defaults.

Evidence:

- Contributor sections, dropped detail, registration surfaces: planner
  defaults, Q1 to Q3.
- Link targets and section owners: the nine sibling plans.
- README wording, the cap, the raw URL: investigation. The personal memory
  store is absent.
