# build-auto-teach
Status: verified
Planned-at: 0e780c742b30813a45303757730d81b0269cd759
Gated-hash: abd0e6fb4308

## Idea

A verified build spawns a clean-context teacher sub-agent that distils the
change's durable knowledge into the workspace wiki, bounded and best-effort.

### Motivation

Build classifies durable knowledge in its Q&A loop but only tells the
orchestrator to route it to `/s:teach`, which nobody runs, so the wiki never
learns from builds and answered queue blocks sit undrained. The user wants a
verified build to teach on its own, only relevant things, and only where a
workspace wiki exists.

### Details

- Add a third named agent role, `teacher`, under `plugins/s/agents/teacher.md`
  with its verbatim twin under `plugins/s/harness/agents/teacher.md`; register
  it in `harness_registry.AGENT_ROLES`.
- Build Phase 5 spawns `s:teacher` right after `set-status verified` when the
  resolved store is a present, non-fallback workspace store and the pipeline
  `build` entry does not declare `teach` false; it runs alongside Phase 6 and
  its report becomes one `wiki:` Observations line in Phase 7.
- Add `teach` (boolean, default true) to the pipeline `build` entry: schema,
  `pipeline-show` renderer, autopilot label and addenda, README grammar.
- Cross-reference the teacher from the teach skill, the harness build
  reference, and the docs; bump the plugin version.

Affected capabilities: `build-spec-lifecycle`, `build-subagent-handoff`,
`harness-registry`, `shipd-config` (modified), `shipd-teach` (added
requirement). Impact: `plugins/s/skills/build/SKILL.md`,
`plugins/s/skills/teach/SKILL.md`, `plugins/s/agents/teacher.md`,
`plugins/s/harness/agents/teacher.md`, `plugins/s/harness/references/build.md`,
`plugins/s/skills/build/scripts/{harness_registry,pipeline_schema,spec_status,autopilot}.py`,
`.shipd/README.md`, `docs/{oracle,customise,harness-agents-reference}.md`,
tests under `plugins/s/skills/build/tests/`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- The interactive `/s:teach` sweep is unchanged; it stays the full write path
  and the only place promotion to a base store and ledger corrections happen.
- No teaching into the repo-local fallback store or the personal memory store.
- No re-teaching of merged delta specs or master requirements; `verified/`
  already holds them.
- No interview, no `wiki-queue-answer`, and no consent-gated capture by the
  agent; a sub-agent cannot obtain the express yes the durability rubric needs.
- No change to the build report's fixed structure; the outcome rides in
  Observations.

## Implementation

- **A self-sufficient agent, not a teach-skill mode.** `s:teacher` carries its
  whole contract in `plugins/s/agents/teacher.md`, mirroring `validator.md`:
  frontmatter `name`/`description`, no `model:` pin, spawn message carrying only
  the change name and the absolute path of the plugin's
  `skills/build/scripts/` directory (`<SCRIPTS_DIR>`). Other harnesses receive
  agent bodies through the registry generator, not skills, and
  `named-agent-types` wants the shipd role visible in the agents pane.
  Rejected: a `--build` mode on `/s:teach` invoked from a generic sub-agent;
  it would not render on non-Claude harnesses.
- **Spawn site and timing.** Phase 5 gains step 7 after the `verified` stamp:
  read `wiki-show --json` from the worktree; spawn only when `present` is true
  and `fallback` is false and the `build` entry's `teach` is not false;
  `subagent_type: s:teacher`, description `teacher · <change>`, model the
  workers' tier (the `subagent_model` policy). Build continues into Phase 6
  without waiting; Phase 7 step 3 collects the report before printing.
  Rejected: blocking before the merge, which adds wall-clock to every build;
  and running after the PR merges, when a driven build's turn may be over.
- **Workspace store only.** A fallback-store write would land inside the
  worktree after the build commit and need a second commit, so the agent never
  writes there. The orchestrator's skip line reads
  `wiki: skipped — no workspace store` (or `— teach disabled by pipeline`).
- **Relevance is the two rubrics.** Candidates are the plan's
  `## Questions and answers` entries answered by USER, `## Implementation`
  decisions whose rationale states a position beyond this change, and answered
  queue blocks (the ledger's `Queued:` slugs first, then any other answered
  block, oldest first). Classify with the knowledge capture rubric; only the
  Durable tier continues to the durability rubric: Include becomes a page,
  Consent-gated is withheld and named in the report, Exclude is dropped. A
  candidate contradicting an existing page writes nothing and files a pending
  block with `wiki-queue-add --origin "build/<change>"`.
- **Bound and bookkeeping.** At most five page touches per run, updating an
  existing page over minting a slug; every page cites `change/<slug>` and any
  `verified/<cap>` it leans on; drained answers land verbatim in a dated
  `sources/` file; `index.md`, `queue.md`, `log.md` staged in full with a
  `## [YYYY-MM-DD] teach | build <change>` entry; advisory answers keep
  `Authority: advisory`. One `spec_emit.py wiki --from` call; on a lint
  finding fix once and re-run, then report `failed`.
- **Output contract.** One line per outcome — `taught — [[slug]] (new|updated):
  <summary>`, `drained — q-<slug>`, `withheld — <item>: consent-gated`,
  `queued — q-<slug>: contradiction with [[page]]`, `skipped — <reason>`,
  `failed — <reason>`, or the single line `nothing durable` — then a one-line
  count. The orchestrator folds it into one Observations line prefixed `wiki:`.
- **Best-effort.** A failed or absent teacher report is an Observations line,
  never a build failure or a merge delay, matching the telemetry rule. A driven
  build awaits the teacher before its final text, per the existing
  no-pending-background rule.
- **`teach` option.** `_BUILD_EXTRA_KEYS` gains `teach`, validated with
  `_is_bool`; `_PIPELINE_OPTION_KEYS` and `_LABEL_OPTIONS` gain `teach` after
  `telemetry`; `_entry_options` adds `- Skip the post-verify teacher: do not
  spawn the `s:teacher` sub-agent.` when false; README grammar names it.
- **Version bump** to `0.6.368` in `plugins/s/.claude-plugin/plugin.json`.

Risk: the teacher reads the change while Phase 6 archives it; `cat change`
resolves `planned/` then `completed/`, so the read survives the move. Risk:
over-capture; the rubric tie-breakers lean to withhold, and every page names
its backing change so a wrong page is traceable and correctable with
`/s:teach`.

## Readiness attestation

### Problem and motivation

Build classifies durable knowledge but never writes it; the wiki learns only
when a human runs `/s:teach`.

Evidence:

- `plugins/s/skills/build/SKILL.md:485-489` routes Durable items "via
  `/s:teach` or the oracle queue" with no step that runs teach.
- Capability `shipd-teach`, requirement `teach-skill`, defines teach as a
  user-invoked interactive flow; the workspace store's `log.md` shows one teach
  run, dated 2026-09-16, against 89 queue blocks.

### Scope and non-goals

The change adds one agent role, one build step, and one pipeline option; the
teach sweep, fallback store, and spec content stay out.

Evidence:

- In scope: `plugins/s/skills/build/SKILL.md:544-549` (the `verified` stamp),
  `plugins/s/skills/build/scripts/harness_registry.py:35`,
  `plugins/s/skills/build/scripts/pipeline_schema.py:51-52`.
- Out of scope: capability `shipd-teach` requirements `teach-gap-interview`,
  `teach-promote-to-base`, `teach-qa-reference` are untouched; capability
  `shipd-wiki` requirement `wiki-autocommit` fixes why fallback writes are
  excluded.

### Affected capabilities and files

Five capabilities and thirteen source files, because the role, the spawn, and
the option each live in a different surface.

Evidence:

- Capability `build-subagent-handoff`: requirement `named-agent-types` (base
  7c1cbc7016c5).
- Capability `harness-registry`: requirement `registry-agent-source` (base
  20ffb2d916f0).
- Capability `shipd-config`: requirements `pipeline-stage-options` (base
  6a0e0b0bcd20) and `pipeline-grammar-docs` (base 7a71820a4748).
- Capabilities `build-spec-lifecycle` and `shipd-teach`: added requirements.
- Files: `plugins/s/skills/build/SKILL.md:446-549,745-800`,
  `plugins/s/skills/teach/SKILL.md:9-20`, `plugins/s/agents/validator.md`
  (template), `plugins/s/harness/agents/`, `harness_registry.py:35`,
  `pipeline_schema.py:51-52,193-202`, `spec_status.py:3458`,
  `autopilot.py:629,886-895`, `.shipd/README.md:340-342`,
  `docs/harness-agents-reference.md:28-33`, `docs/customise.md:140-142`,
  `docs/oracle.md:50-55,222-226`, tests `test_harness_registry.py:300`,
  `test_subagent_contract.py:378-382`, `test_pipeline_schema.py:65-68`,
  `test_pipeline_show.py:175`, `test_autopilot.py:2416-2488`.
- Runnable premise: `spec_status.py wiki-show --json` from the worktree exited
  0 and reported `present: true`, `fallback: false`, `personal: false`.
- Runnable premise: `spec_status.py cat change oracle-inline-lookup` exited 0
  and printed the archived `completed/2026-10-27-oracle-inline-lookup/plan.md`.
- Runnable premise: `spec_status.py pipeline-show --json` exited 0 with
  `source: default` and six bare stages.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Agent over skill mode: settled by investigation of `named-agent-types` and
  the registry generator's per-role rendering.
- Workspace store only: settled by investigation of `wiki-autocommit`'s
  fallback rule and the build commit order.
- Concurrent spawn, awaited at the report: settled by investigation of the
  telemetry best-effort rule and the driven-build foreground rule.
- Relevance via the two rubrics and draining answered blocks within the bound:
  settled by investigation of `capture-rubric.md` in the epic and ask skills
  and the workspace queue's answered blocks.
- `teach` opt-out on the build entry: settled by investigation of the
  `validator` and `telemetry` precedent in `pipeline-stage-options`.
