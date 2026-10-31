# init-skill
Status: verified
Epic: shipd-init
Planned-at: 191ef2030e4fd6e5268c03e2725cc744f545098f
Gated-hash: 1e0fe89205c5

## Idea

Add the `/s:init` setup skill and one shared needs-setup reference that every
layout-requiring skill routes through.

### Motivation

A user starting shipd in a new project has no guided setup and must hand-edit
JSON for every choice, while seven skills each meet a missing layout their own
way, from stopping cold to wrongly claiming it appears on first merge.

### Details

- New skill `plugins/s/skills/init/` (`SKILL.md`, `references/needs-setup.md`,
  `references/constitution-starter.md`) and body `harness/bodies/init.md`.
- `plan`, `epic`, `research`, `autopilot`, `status`, `initiative`, `build`:
  SKILL.md and body swap their layout passage for the reference.
- New contract test `test_init_skill_contract.py`.
- `README.md`, `docs/cheatsheet.md`, `AGENTS.md`, `docs/getting-started.md`
  list the skill; `plugin.json` version bump.

Affected capabilities: `shipd-init` (added), `shipd-plan` (modified
`missing-layout-guard`).

### Non-goals

- No engine code: `init-status` (member `init-status`) and `shipd config set`
  (member `config-control`) are consumed as planned there.
- No new config keys, no GitHub-side setup, no `/s:onboard` change.
- Workspace, wiki, hook, and gate setup logic stays in its own verbs and skills.

## Implementation

- **Sections** (Q2): `layout` and `config` are the wizard's config steps;
  `workspace`, `wiki`, `memory`, `hooks`, `gate` are on-demand hand-offs. The
  constitution is the wizard's last step, not a section (Q1). Keys, order,
  options, and default writes: `artefacts/wizard-keys.md`.
- **Binary and verbs.** SKILL.md resolves `shipd` on PATH, else
  `${CLAUDE_PLUGIN_ROOT}/bin/shipd`, as `/s:worktree-hooks` does. Writes run
  `shipd config set <key> <value>` with no `--layer`, so config-control's
  default layers pick the file (config-control Q2: `guardrails` lands in the
  repo; `memory_dir`, `wiki_base`, `voice` in the user file per the epic).
  Values pass unquoted (config-control Q3). Layout runs `python3
  .../spec_status.py init`.
- **Set detection.** A key is set when `shipd config` prints it with a file
  path in brackets, unset when absent or `[default]` (observed below).
- **Dialogs.** One AskUserQuestion per key, brief in the question text and
  option descriptions per `question-brief.md`, current value first; Other
  carries free-text paths. Accepted defaults are written (Q5) except where
  the default is absence. Bare `/s:init` on a set-up project runs the same
  wizard skipping set keys and says "nothing left to set up" when none remain
  (Q6). Rejection: relay stderr `error:`/`hint:`. When every `error:` names
  the key being set, ask it once more, then skip it with a note. When one
  names another key, offer to fix that key first, then retry once.
- **Constitution** (Q4): offered only when `<content-dir>/constitution.md` is
  absent; the skill reads `content_dir` from `init-status --json` and copies
  the starter with `cp -n`. Rejected: a new engine verb, outside this
  member's no-engine-code scope.
- **Needs-setup reference.** Runs `spec_status.py init-status`, acting on
  `action:` (init-status Q1); adds `--unattended` when the prompt says no
  human is available (Q3, init-status Q3). `wizard` invokes `/s:init` by
  reference, then re-runs `init-status`; continuing needs `action: none`, and a
  user who stops the wizard stops the calling skill. Runs from the root the
  skill writes into: the worktree for plan, research, epic, and build.
- **Roster wiring.** Each roster SKILL.md keeps one inline sentence naming
  the check plus the pointer (the always-applies pattern); bodies get one
  sentence. `/s:plan`'s stop list replaces "Missing content-directory layout"
  with "First-run setup". `/s:initiative` applies it to `set` only.
- **Contract test** mirrors `test_plan_deep_skill_contract.py`: frontmatter
  name, body marker, sole `"/s:init"` claimant, registry files, roster
  pointers, retired phrases absent (whitespace-normalized), starter is
  commented, reference names all three actions and `--unattended`.

Risk: the sibling members merge first (epic `After`); verbs are named as
their plans define them.

## Questions and answers

### Q1: Is the constitution its own /s:init section?
- **Question:** Options: (1) a wizard-only step; (2) a `constitution`
  section too. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** A wizard-only step: the full wizard offers the starter, and no
  partial init writes one.
- **Cited:** queue q-init-constitution-scaffold

### Q2: Which sections does /s:init expose?
- **Question:** Options: (1) `layout`, `config`, and on-demand `workspace`,
  `wiki`, `memory`, `hooks`, `gate`; (2) one section per wizard step.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1, matching the epic's design diagram and its
  `/s:init config` success criterion.
- **Queued:** q-init-skill-sections

### Q3: Does the needs-setup check pass --unattended in-session?
- **Question:** Options: (1) pass it when the invocation says no human is
  available or the run is unattended; (2) rely on `SHIPD_UNATTENDED` alone.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1: in-session sub-agents cannot inherit the variable,
  and their prompts already say no human is available.
- **Queued:** q-needs-setup-unattended-flag

### Q4: How is the constitution starter written?
- **Question:** Options: (1) the skill copies a shipped starter only when
  absent; (2) a new engine verb.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1; `/s:worktree-hooks` already authors content-directory
  files itself, and `cp -n` cannot overwrite.
- **Queued:** q-init-constitution-write-path

### Q5: Does accepting a default write it?
- **Question:** Options: (1) write it through `shipd config set`; (2) leave
  the key unset.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1, so the step counts as set next time; a default that
  is the key's absence writes nothing.
- **Queued:** q-init-wizard-accepted-default

### Q6: What does bare /s:init do on a set-up project?
- **Question:** Options: (1) run the wizard skipping set keys; (2) print the
  status and section list only.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1; it also reaches a missing constitution.
- **Queued:** q-init-bare-on-ready-project

## Readiness attestation

### Problem and motivation

No guided setup exists, and seven skills handle a missing layout divergently.

Evidence:

- Epic `shipd-init` Introduction and Decisions "/s:init is a front door" and
  "One shared needs-setup reference".
- Passages: `plan/SKILL.md:59-73`, `research/SKILL.md:30-36`,
  `epic/SKILL.md:22-26`, `autopilot/SKILL.md:17`, `status/SKILL.md:16`,
  `initiative/SKILL.md:25-27`, `build/SKILL.md:52-56`.

### Scope and non-goals

Skill text, one reference, one starter, one test, and docs; no engine code.

Evidence:

- Engine verbs come from `.worktrees/init-status` and
  `.worktrees/config-control` plans.
- Bodies to edit: `harness/bodies/{plan,research,epic,autopilot,status,initiative,build}.md`.

### Affected capabilities and files

Two capabilities; 23 files plus a new test.

Evidence:

- `shipd-init` new; `shipd-plan` `missing-layout-guard` base 52592b01ec26
  from `spec_status.py base-hash`.
- Roster tests a new skill meets: skill descriptions, question brief,
  plan-mode guard, harness bodies, prompt notation.
- Runnable premise: in a temp repo with `{"pr-mode": "draft"}`, `shipd
  config` → exit 0, `pr-mode = "draft"  [<repo>/.shipd-config.json]` and
  `dir = ".shipd"  [default]`.
- Runnable premise: `shipd init` there → exit 0, `all shipd directories are
  ready`; `shipd init status` → exit 2 today (init-status unmerged).

### No open task-shaping decision

Q1 settled by the oracle; Q2 to Q6 were answered by the user, who accepted each recommendation.

Evidence:

- Wizard order, sections' verbs, and unattended behaviour come from the
  epic's Decisions; keys from `artefacts/wizard-keys.md`.
