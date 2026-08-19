# harness-command-bodies
Status: verified
Epic: harness-install

## Idea

Add the shared, feature-gated command-body source — one distilled template
per `/s:` command plus fallback reference templates — and the stdlib render
function that composes a body for a declared feature set.

### Motivation

The harness-install epic's generation pipeline renders every harness's
command files from one body source scaled by declared features, but no such
source or render function exists; without it the `harness-verb` member has
nothing to generate.

### Details

- Template data under `plugins/s/harness/`: `bodies/<command>.md` for all
  seventeen `/s:` commands, `bodies/_preamble.md` (shared partial), and
  `references/<command>.md` fallback files for commands with gated segments.
- New engine module `plugins/s/skills/build/scripts/harness_bodies.py`:
  gate parsing and `render(command, features, refs_dir=None)`.
- Tests at `plugins/s/skills/build/tests/test_harness_bodies.py`; plugin
  version bump.

Affected capabilities: `harness-command-bodies` (added). Impact:
`plugins/s/harness/` (new directory tree),
`plugins/s/skills/build/scripts/harness_bodies.py` (new),
`plugins/s/skills/build/tests/test_harness_bodies.py` (new),
`plugins/s/.claude-plugin/plugin.json` (version bump). Depends on
`harness_registry.FEATURES` from the harness-registry member (merges before
this change builds). No new dependencies.

### Non-goals

- No file generation into repositories or user-global dirs — that is the
  `harness-verb` member; this member only produces strings.
- No registry edits — dialects, paths, and feature declarations stay in
  `harness_registry.py`.
- No verbatim SKILL.md ports — bodies are distilled routers, per the epic.
- No new `shipd` verbs and no changes to existing capabilities' specs.

## Implementation

- **Template home:** `plugins/s/harness/` — plugin data beside `skills/`,
  not inside the engine-scripts dir (the constitution's stdlib rule binds
  scripts; templates are content). The render module resolves it relative
  to its own location (`../../../harness/`), which works from a checkout and a
  cache snapshot alike (the wordmark module's pattern).
- **Gate syntax (minimal, markdown-safe):** whole-line HTML-comment markers
  `<!-- if:<feature> -->`, optional `<!-- else -->`, `<!-- end -->` —
  non-nesting; plus `<!-- include:preamble -->` (replaced by
  `_preamble.md`'s content) and the literal `{refs}` placeholder. Rejected:
  a templating dependency — stdlib line scanning is enough for flat gates.
- **`render(command, features, refs_dir=None)`:** loads
  `bodies/<command>.md`, resolves includes, keeps an `if:` segment when its
  feature is in `features` (else the `else` segment when present), strips
  all marker lines, and substitutes `{refs}` with `refs_dir`. When
  `refs_dir` is `None` and a kept segment contains `{refs}`, raise — the
  caller must supply it; gate names not in `harness_registry.FEATURES`
  raise `ValueError` naming the template and line. `commands()` returns the
  sorted template ids (the bodies dir listing minus `_`-prefixed partials).
  `reference(command)` returns the fallback file's text or `None`.
- **The never-mention rule is testable:** for every command,
  `render(command, ())` must not contain the tokens `subagent`,
  `sub-agent`, `AskUserQuestion`, or `{refs}`; and gated-feature text may
  only appear inside its gate. Fallback pointers (`read {refs}/<command>.md
  …`) sit inside `<!-- if:file-references -->`; the `else` branch carries
  the inline three-step degradation note (acknowledge the missing
  capability → state what would have run → offer the manual workaround).
- **Preamble:** `_preamble.md` opens every body: the command's one-line
  purpose slot, then the canonical engine-resolution snippet —
  `S="$HOME/.claude/plugins/cache/shipd/s/$(ls "$HOME/.claude/plugins/cache/shipd/s" | sort -t. -k1,1n -k2,2n -k3,3n | tail -1)/skills/build/scripts"`
  — so bodies drive `shipd` for read verbs and `python3 "$S/<script>"` for
  lifecycle mutations (`spec_emit.py`, `spec_gate.py`, `spec_merge.py`),
  which the curated binary deliberately does not expose.
- **Distillation constraints (binding on every body):** router pattern — a
  lean numbered workflow (target under ~80 lines rendered), driving the
  `shipd` CLI and the engine scripts via `$S`; second person, imperative;
  no Claude Code tool names outside gates; each body ends by naming its
  follow-up command (plan → build, review → fix loop, etc.). Builders read
  the command's `plugins/s/skills/<command>/SKILL.md` and distill to these
  constraints around the per-command core workflows:

  | command | ungated core workflow the body encodes |
  | --- | --- |
  | plan | investigate repo → author plan/deltas/tasks in a staging dir → `python3 "$S/spec_emit.py" change` → `python3 "$S/spec_gate.py"` |
  | build | read planned change → implement tasks in order (`claim_task.sh` loop) → tests → `python3 "$S/spec_merge.py"` → PR |
  | review | `git diff` vs base → structured semantic review by cohort → severity verdict |
  | status | `shipd status` / `shipd list` / `shipd validate` readouts |
  | doctor | `shipd doctor` → apply consented remedies → re-run |
  | epic | investigate → author `.shipd/epics/<slug>/epic.md` per its contract → `shipd lint --epic` equivalent via `$S/spec_lint.py --epic` |
  | research | decompose question → web research → cited report installed via `$S/spec_emit.py` research flow per its skill |
  | workspace | `shipd workspace` readout; init/clone/sync via `$S/spec_status.py` workspace verbs |
  | initiative | initiative CLI verbs via `$S/spec_status.py` per its skill |
  | ask | shape one compact question → consult wiki surfaces via `$S/spec_status.py cat wiki` → cited answer or queue |
  | teach | scan spec surfaces → distill wiki pages → staged `$S/spec_emit.py wiki` |
  | remember / memory / forget | personal store add / list / remove via the `--personal` wiki verbs |
  | autopilot | preflight epic → run `$S/autopilot.py` with confirmed budgets |
  | onboard | the nine-step guided tour, driven from its skill's step files |
  | video-ingest | `video_ingest.py` doctor → bundle → extract → grounded brief install |

  These rows anchor scope; the SKILL.md remains each body's source of
  truth for detail.
- **Gated segments (where the four features actually bite):** `subagents` —
  build's delegated executor/validator flow (else: single-agent build);
  `question-dialogs` — plan/epic/doctor's interactive rounds (else: typed
  numbered questions in chat); `file-references` — every fallback pointer
  and progressive-disclosure read (else: inline notes); `background-tasks`
  — build's parallel task groups and watches (else: sequential foreground).
- **Version bump:** `plugins/s/.claude-plugin/plugin.json` to the next
  patch above the value the branch carries after its base merge (expected
  `0.6.139` → `0.6.140`; harness-registry ships `0.6.139` first).

Risk: seventeen distilled bodies drift in tone/size — bounded by the
constraints above and the tests' size/token checks; content quality beyond
that is reviewed at the PR gate. Risk: `harness_registry` unmerged at build
time — the supersession gate's base merge precedes any execution, and the
import fails loudly if not.
