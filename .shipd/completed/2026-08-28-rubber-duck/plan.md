# rubber-duck
Status: verified

## Idea

Add `/s:duck` — the Rubber Duck agent: a read-only, slightly adversarial
conversational skill for talking through ideas and validating processes and
concepts before any work is planned or built.

### Motivation

shipd covers every delivery stage from research to review, but nothing supports
the ideation stage before `/s:plan` — an idea today goes straight to artifacts
or nowhere. The installed report `research/ai-rubber-duck-dx` names this
"solution vending machine" gap and grounds the critic pattern the skill adopts.

### Details

- New skill `plugins/s/skills/duck/SKILL.md` (`/s:duck [topic]`): a
  Generator-Critic conversation — the user generates, the duck critiques. The
  first reply of a session opens `🦆 Rubber Duck agent — shipd:duck v<version>`;
  later replies drop the banner.
- Strictly read-only: the duck may read the repo and the engine-mediated spec
  surfaces to ground its critique, but never edits files, writes artifacts,
  runs mutating commands, or invokes other skills.
- Critique protocol from the research report: challenge assumptions, surface
  the strongest alternative, triage critiques as blocking / non-blocking /
  suggestion, suppress style trivia, end every reply with exactly one primary
  question.
- Handoff awareness: the duck knows the shipd roster and names the right exit
  (`/s:research`, `/s:epic`, `/s:plan`, `/s:fix`, `/s:ask`) when the
  conversation converges; a wrap-up cue produces a response-text debrief.
- New harness body `plugins/s/harness/bodies/duck.md` — bodies/skills roster
  parity is test-enforced.
- Docs: one-line rows in `README.md`'s command table and `docs/cheatsheet.md`,
  plus the AGENTS.md roster sentence. Plugin version bump to 0.6.157.

Affected capabilities: `shipd-duck` (added). Impact:
`plugins/s/skills/duck/SKILL.md`, `plugins/s/harness/bodies/duck.md`,
`plugins/s/.claude-plugin/plugin.json`, `README.md`, `docs/cheatsheet.md`,
`AGENTS.md`; the report `research/ai-rubber-duck-dx` is already installed on
this branch. No engine or script changes; no new dependencies.

### Non-goals

- No implementation, artifact emission, or file mutation from the duck — ever;
  converged ideas exit through the named skills.
- No new engine verbs and no pipeline stage — the duck sits before the
  pipeline, it is not part of it.
- No multi-model council, voting, or cross-model debate (the report's MCP
  `duck_council` patterns) — one session, one critic.
- No formal lite/full/ultra intensity argument — one default posture with
  verbal dials.
- No AskUserQuestion dialogs — plain conversation; the skill stays off the
  `shipd-interaction` recovery roster.

## Implementation

- **Generator-Critic split, critic read-only** (report §Evaluator-Optimizer):
  the duck analyses, validates, and questions but alters nothing — no
  Edit/Write, no mutating Bash, no emit or status-mutating verbs, no skill
  invocation. It may run read-only exploration (file reads,
  `spec_status.py cat …`) so critique is grounded in the actual repo. Rejected:
  a pure-chat duck with no repo reads — the report's AGENTS.md-context finding
  shows ungrounded critics give misaligned, generic advice.
- **Slightly adversarial, not a strict Socratic tutor**: the duck states
  assessments and takes positions (the request asks it to steer toward the
  best option), but must not smuggle full designs or produce implementation
  code; pushback leads with concrete alternatives. Verbal dials adjust
  intensity ("go easy" softens, "grill me" hardens). Rejected: a
  hint-withholding tutor with formal lite/full/ultra levels — that optimizes
  pedagogy; this optimizes decision quality, and levels add surface for v1.
- **Reply discipline against over-compliance** (report benchmark: unprompted
  models leak the solution 44% of the time): at most three critique points per
  reply, each labeled blocking / non-blocking / suggestion; style and naming
  trivia suppressed; every reply ends with exactly one primary question. The
  first session reply opens with `🦆 Rubber Duck agent — shipd:duck
  v<version>`, the version read from
  `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` per the sibling
  version-announce convention.
- **Handoff by name, never invocation**: SKILL.md carries a compact exit map —
  un-cited external unknowns → `/s:research`; a multi-change feature →
  `/s:epic`; a single buildable change → `/s:plan`; a reported defect →
  `/s:fix`; a decision wanting mikk's standing opinion → `/s:ask`. On a
  wrap-up cue the duck prints a debrief — problem, options considered,
  recommendation with rationale, known risks, suggested next command — as
  response text only, no files.
- **Harness body**: `plugins/s/harness/bodies/duck.md` opens with the required
  `<!-- description: … -->` marker and is gate-free (no `if:` features), so no
  `references/duck.md` fallback is owed. Runnable premise, observed: `python3
  -m unittest discover -s plugins/s/skills/build/tests -p
  "test_harness_bodies.py"` ran 26 tests, OK — the parity suite passes today
  and discovers bodies by directory listing, so it fails when `skills/duck/`
  exists without a body and passes once the body lands.
- **Research grounding is a branch artifact**: `research/ai-rubber-duck-dx/
  report.md` was installed through `spec_emit.py research` during planning
  (observed: exit 0, "installed research ai-rubber-duck-dx"). SKILL.md cites
  it as the design source but does not read it at runtime — the behavior is
  compiled into the skill text, per the report's progressive-disclosure
  section.

Risk: over-compliance drift — the duck slipping into writing the solution.
Guarded by the delta's restraint scenarios and by the reply-discipline rules
living in SKILL.md itself, mirroring the constraints the report benchmarked as
necessary.
