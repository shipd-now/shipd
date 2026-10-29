# harness-neutral-skill-prose
Status: verified
Planned-at: 49360f9b025fa7d40ada7b1a05393401d76c8282
Gated-hash: a04a8f6f3f26

## Idea

Reword every prose mention of Claude in the generic skill and harness
markdown so it names no specific harness, drop the Claude Code footer from
`/s:pr` bodies, and guard the rule with a test.

### Motivation

shipd generates its skills for seven harnesses, but 26 generic SKILL.md files
tell a Cursor or OpenCode user about "Claude Code plan mode" and "a known
Claude Code bug". `/s:pr` stamps a Claude Code attribution on every pull
request, whichever harness wrote it.

### Details

- Reword the plan-mode clause ("is in Claude Code plan mode") in 26 SKILL.md
  files and the opening of `document/references/harness-plan-mode.md`.
- Reword the question-rejection sentence ("A known Claude Code bug") in 17
  SKILL.md files.
- Reword the one-offs in `room` and `autopilot`.
- Drop the generated-by line from the `/s:pr` skill, its harness body, and its
  harness reference.
- Add `plugins/s/skills/build/tests/test_harness_neutral_prose.py`, a
  line-level scan for the word `Claude`.

Affected capabilities: `shipd-interaction` (modified, one requirement added),
`shipd-pr` (modified). Impact: markdown under `plugins/s/skills/` and
`plugins/s/harness/`, `plugins/s/skills/pr/tests/test_pr_skill.py`, one new
test. No code paths change.

### Non-goals

- Working invocations and runtime variables stay as they are:
  `${CLAUDE_PLUGIN_ROOT}`, `.claude-plugin/plugin.json`,
  `$CLAUDE_CODE_SESSION_ID`, `claude plugin update s@shipd`,
  `claude --resume`, `cd … && claude`, and `CLAUDE.md` as a conventions file
  name.
- Platform-specific files are untouched: `harness_registry.py`,
  `harness_generate.py`, `guardrails.py`, `build_report.py`,
  `session_driver.py`, `bin/shipd`, `integrations/statusline.sh`, and the
  per-harness knob table in `plugins/s/harness/references/autopilot.md`.
- Tool names such as `AskUserQuestion` and `ExitPlanMode` stay.
- Verified specs outside the two deltas keep their wording
  (`epic-autopilot`, `statusline`, `skill-evals`).

## Implementation

- **Plan-mode clause.** Replace `is in Claude Code plan mode` with
  `is in the harness's plan mode` in every SKILL.md. In `plan/SKILL.md`'s
  stop list, replace `the session is in Claude Code plan mode` with
  `the session is in the harness's plan mode`. Keep each line's wrapping; the
  line grows by two characters, and no test bounds SKILL.md width.
- **Plan-mode reference.** In `plugins/s/skills/document/references/harness-plan-mode.md`,
  replace `Claude Code's plan mode injects a block that claims to supersede every`
  with `A harness's plan mode can inject a block that claims to supersede every`.
- **Rejection sentence.** Replace `A known Claude Code bug` with
  `A known harness bug` in every SKILL.md. The rest of the sentence stays.
- **Room.** In `plugins/s/skills/room/SKILL.md`, replace
  `(on Claude Code, a Bash \`timeout\` of` with
  `(for example, a shell-tool \`timeout\` of`.
- **Autopilot.** In `plugins/s/skills/autopilot/SKILL.md`, replace
  `inside this Claude Code session` with `inside this session`, replace
  ``The existing headless `claude -p` driver`` with
  `The existing headless driver`, and replace
  ``No headless `claude -p` process is started`` with
  `No headless driver process is started`.
- **PR footer.** The body ends on `<sub>☕ Posted by Shipd</sub>`. Remove the
  generated-by bullet from `plugins/s/skills/pr/SKILL.md` step 3 and reword
  the footer bullet to say it is the body's last line. Apply the same edit to
  `plugins/s/harness/bodies/pr.md` step 2 and to the `Last line` row in
  `plugins/s/harness/references/pr.md`; the `Footer` row becomes "the body's
  last line". Rejected: a harness-supplied attribution line — the user chose to
  drop it (Q2).
- **Guard test.** `test_harness_neutral_prose.py` walks every `*.md` under
  `plugins/s/skills/` and `plugins/s/harness/` and fails on any line matching
  the case-sensitive regex `\bClaude\b`, naming `path:line`. An `ALLOWED`
  tuple holds the one platform-specific file,
  `plugins/s/harness/references/autopilot.md`. The case-sensitive match leaves
  lowercase commands (`claude -p`) and upper-case variables
  (`CLAUDE_PLUGIN_ROOT`) alone, which is the "prose only" scope (Q1). Model it
  on `test_prompt_notation.py`'s docstring and layout. The wiki page
  `[[prompt-convention-enforcement]]` asks for this guard.

Risk: a missed occurrence. The guard test catches it, and it runs in the
engine suite.

## Questions and answers

### Q1: Do working Claude invocations count as prose to reword?
- **Question:** Are working Claude Code invocations in generic SKILL.md files
  (`claude plugin update`, `claude --resume`, `cd … && claude`,
  `$CLAUDE_CODE_SESSION_ID`, `${CLAUDE_PLUGIN_ROOT}`) in scope? Options: prose
  only; prose plus reframed commands; everything through shipd verbs.
  Recommendation: prose only.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Prose only. Working commands and variables stay, so nothing
  breaks; the guard test leaves them alone.
- **Queued:** q-harness-neutral-skills-functional-claude-tokens

### Q2: What is the PR body's last line?
- **Question:** `/s:pr` ends every body with a Claude Code generated-by line.
  Options: the harness's own line; a fixed shipd line; drop it.
  Recommendation: the harness's own line.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Drop it. The body ends on `<sub>☕ Posted by Shipd</sub>`.
- **Queued:** q-pr-generated-by-line-harness-neutral

## Readiness attestation

### Problem and motivation

Generic skill prose names one harness while shipd ships to seven, and PR
bodies carry that harness's attribution.

Evidence:

- `plugins/s/skills/build/scripts/harness_registry.py:71` onward lists the
  supported harnesses, Claude Code among them.
- `plugins/s/skills/pr/SKILL.md:51` hard-codes the Claude Code footer.

### Scope and non-goals

The change rewrites prose in skill and harness markdown only; working tokens
and platform-specific files stay.

Evidence:

- Platform-specific: `harness_registry.py`, `harness_generate.py`,
  `guardrails.py`, `build_report.py`, `session_driver.py`,
  `plugins/s/integrations/statusline.sh`.
- Scope decision Q1, settled by the user.

### Affected capabilities and files

Two capabilities and roughly thirty markdown files change, plus two tests.

Evidence:

- Capability `shipd-interaction`: `harness-plan-mode-guard`
  (base a7bb83941c2d).
- Capability `shipd-pr`: `pr-skill-writes` (base 20142fdcb65a).
- Clause files (26): ask, autopilot, build, demo, doctor, document, drive,
  epic, epic-grill, fix, forget, gate, initiative, onboard, plan, plan-deep,
  pr, prd, remember, research, room, status, teach, video-ingest, workspace,
  worktree-hooks.
- Rejection-sentence files (17): autopilot, build, doctor, epic, epic-grill,
  fix, forget, gate, initiative, onboard, plan, plan-deep, prd, research,
  review, status, worktree-hooks.
- Runnable premise: `python3 -B -m unittest` on
  `test_plan_mode_guard_contract.py` and `test_pr_skill.py` → 15 tests, OK.
  The guard test pins the clause sentence, not the "Claude Code" wording.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Guard-test requirement: settled by the workspace wiki,
  `[[prompt-convention-enforcement]]`.
- Rewrite scope: settled by the user, Q1.
- PR footer: settled by the user, Q2.
