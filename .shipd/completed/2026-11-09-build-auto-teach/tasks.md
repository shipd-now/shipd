## 1. The teacher role

- [x] 1.1 [req: registry-agent-source] In
      `plugins/s/skills/build/tests/test_harness_registry.py`, change
      `test_agent_roles_exclude_the_retired_oracle` to assert `hr.AGENT_ROLES ==
      ("sub-agent", "validator", "teacher")`. In
      `plugins/s/skills/build/tests/test_subagent_contract.py`, extend
      `test_harness_twins_match_bodies` to loop over `teacher.md` too. Run both
      files and observe them fail — the role and files do not exist yet.
- [x] 1.2 [req: teacher-agent-contract] In
      `plugins/s/skills/build/tests/test_subagent_contract.py`, add a
      `TeacherContractTest` reading `plugins/s/agents/teacher.md` that asserts:
      the frontmatter has `name: teacher` and no `model:` line; the body names
      `cat change`, `wiki-show --json`, `cat wiki index`, `cat wiki queue`,
      `capture-rubric.md`, `spec_emit.py`, `wiki --from`, `wiki-queue-add`,
      `--origin "build/<change>"`, the phrase `at most five`, and each output
      line head `taught —`, `drained —`, `withheld —`, `queued —`, `skipped —`,
      `failed —`, `nothing durable`; and that a `## Guardrails` section contains
      `never` alongside `in place`, `wiki-queue-answer`, and `git`. Run it and
      observe it fail.
- [x] 1.3 [req: teacher-agent-contract, named-agent-types] Create
      `plugins/s/agents/teacher.md` with frontmatter `name: teacher` and a
      one-line `description`, no `model:`, and a body in the shape of
      `plugins/s/agents/validator.md` carrying the full contract from
      `plan.md` `## Implementation`: the spawn message (change name and
      `<SCRIPTS_DIR>` only), `## Your inputs (and only these)` listing the engine
      reads and the two rubric paths
      (`<SCRIPTS_DIR>/../../epic/references/capture-rubric.md`,
      `<SCRIPTS_DIR>/../../ask/references/capture-rubric.md`), the store gate
      (`wiki-show --json` must report `present` true and `fallback` false, else
      `skipped — <reason>`), the candidate list and rubric routing, the
      contradiction rule with `wiki-queue-add … --origin "build/<change>"`, the
      five-page bound and bookkeeping (full `index.md`/`queue.md`/`log.md`,
      dated `sources/`, `Authority: advisory`, `change/<slug>` citations, log
      entry `## [YYYY-MM-DD] teach | build <change>`), the single
      `spec_emit.py --root <repo-root> wiki --from <staging>` write with one
      fix-and-retry, the `## Output contract` lines, and `## Guardrails`
      forbidding in-place store edits, questions, `wiki-queue-answer`,
      repository or artifact edits, and git. Use `.shipd/` notation for the
      content directory as the other agents do.
- [x] 1.4 [req: registry-agent-source] Create
      `plugins/s/harness/agents/teacher.md` opening with
      `<!-- description: <the same one line> -->` followed by the body of
      `plugins/s/agents/teacher.md` after its frontmatter, verbatim. Set
      `AGENT_ROLES = ("sub-agent", "validator", "teacher")` in
      `plugins/s/skills/build/scripts/harness_registry.py`. Confirm the tests
      from 1.1 and 1.2 pass and `python3 -m unittest discover -s
      plugins/s/skills/build/tests -p "test_harness_*.py"` stays green.

## 2. The `teach` pipeline option

- [x] 2.1 [req: pipeline-stage-options] In
      `plugins/s/skills/build/tests/test_pipeline_schema.py`, add `"teach":
      False` to the entry in `test_declared_options_are_carried_verbatim` and add
      a test asserting `validate_entries([{"stage": "build", "teach":
      "maybe"}])` raises `ValueError` whose message names `teach`. In
      `plugins/s/skills/build/tests/test_pipeline_show.py`, add a test that a
      declared build entry with `"teach": false` renders `teach=false` after
      `telemetry=false` on the build line. In
      `plugins/s/skills/build/tests/test_autopilot.py`, add `"teach": False` to
      `BUILD_OPTS` and assert the dry-run label contains `teach off` and the
      build addenda contain `s:teacher`. Run them and observe the failures.
- [x] 2.2 [req: pipeline-stage-options] In
      `plugins/s/skills/build/scripts/pipeline_schema.py`, add `"teach"` to
      `_BUILD_EXTRA_KEYS` and a `_is_bool` check emitting
      ``("teach", "`teach` must be a boolean")`` after the telemetry check. Add
      `"teach"` after `"telemetry"` in `_PIPELINE_OPTION_KEYS`
      (`plugins/s/skills/build/scripts/spec_status.py`) and in `_LABEL_OPTIONS`
      (`plugins/s/skills/build/scripts/autopilot.py`). In `autopilot.py`'s
      `_entry_options`, after the telemetry line, append `- Skip the post-verify
      teacher: do not spawn the `s:teacher` sub-agent.` when
      `entry.get("teach") is False`. Confirm the 2.1 tests pass.
- [x] 2.3 [req: pipeline-grammar-docs] In `.shipd/README.md`, extend the
      `build` option line to read `subagent_model` (same tier type as `model`),
      `validator` (boolean, default `true`), `telemetry` (boolean, default
      `true`), `teach` (boolean, default `true`), and `parallelism` (integer
      >= 1), and add one sentence after the defaults paragraph: `teach` false
      skips the post-verify teacher that distils a verified change into the
      workspace wiki.

## 3. Build and teach skill wiring

- [x] 3.1 [req: post-verify-teach, named-agent-types] In
      `plugins/s/skills/build/tests/test_subagent_contract.py`, add a
      `BuildTeacherWiringTest` reading `BUILD_SKILL` that asserts the text
      contains `subagent_type: s:teacher`, `teacher · <change>`, `wiki-show
      --json`, `wiki: skipped — no workspace store`, `wiki: skipped — teach
      disabled by pipeline`, and the phrase `never blocks`. Run it and observe it
      fail.
- [x] 3.2 [req: post-verify-teach] In `plugins/s/skills/build/SKILL.md`,
      Phase 5, add step 7 after the `set-status verified` step, titled
      **Spawn the teacher**: run `spec_status.py wiki-show --json` from the
      worktree and read `present` and `fallback`; when the verb fails,
      `present` is false, or `fallback` is true, record
      `wiki: skipped — no workspace store` for Phase 7; when the `build` entry
      resolved in Phase 0 declares `teach` false, record `wiki: skipped — teach
      disabled by pipeline`; otherwise spawn the Agent tool with
      `subagent_type: s:teacher`, description `teacher · <change>`, `model` the
      workers' tier per the Phase 3 policy, and a spawn message carrying only the
      change name and the absolute `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts`
      path (resolve it first); do not wait — continue to Phase 6.
- [x] 3.3 [req: post-verify-teach] In `plugins/s/skills/build/SKILL.md`,
      Phase 7 step 3, add before the report shape: collect the teacher's report
      (wait for it when still running) and render it as the first Observations
      line, prefixed `wiki:` — `wiki: taught [[a]], [[b]]; drained q-x; withheld
      <n>` from its lines, `wiki: nothing durable`, the recorded skip line, or
      `wiki: teacher failed — <reason>` when it failed or returned nothing;
      state that the teacher never blocks the merge or the report. Extend the
      driven-build paragraph in step 4 with one sentence: the teacher is awaited
      before the final report text. Add an Operating rules bullet: the teacher
      is best-effort, like telemetry. In Phase 4's **Durable** bullet, add that
      the post-verify teacher picks durable items up from the plan's ledger and
      the answered queue, so recording them there is enough. Confirm 3.1 passes.
- [x] 3.4 [req: teacher-agent-contract] In `plugins/s/skills/teach/SKILL.md`,
      after the paragraph that opens "You never write into the store", add a
      short paragraph: a verified build spawns the `s:teacher` agent
      (`plugins/s/agents/teacher.md`), which distils that one change into the
      workspace store with no interview and at most five pages, and skips
      fallback stores; this skill remains the full sweep, the only path for
      promotion to a base store, and the only path for `<change> Q<n>`
      corrections. Keep the file's `description` unchanged.
- [x] 3.5 [req: post-verify-teach] In `plugins/s/harness/references/build.md`,
      add a `## The post-verify teacher` section before `## Shipping modes`
      summarising step 7's gate, the spawn, and the `wiki:` Observations line,
      naming the neutral agent id `shipd-teacher`.

## 4. Documentation

- [x] 4.1 [req: registry-agent-source] In `docs/harness-agents-reference.md`,
      add the row `| `shipd-teacher` | The teacher a verified build spawns to
      distil the change's durable knowledge into the workspace wiki. |` to the
      roles table. In `docs/customise.md`, change the sentence naming the agent
      files to list `shipd-sub-agent`, `shipd-validator`, and `shipd-teacher`.
- [x] 4.2 [req: post-verify-teach] In `docs/oracle.md`, revise the sentence
      "`/s:teach` later distills the captured queue entries into proper wiki
      pages" to say that a verified build's teacher drains answered entries
      into pages automatically where a workspace wiki exists, and `/s:teach`
      remains the full sweep. Revise the "Corrections go through `/s:teach`"
      paragraph so it no longer calls teach the sole distiller: builds also
      distil, corrections still go through `/s:teach`. Run `python3
      plugins/s/skills/document/scripts/docs_lint.py docs/oracle.md
      docs/customise.md docs/harness-agents-reference.md` and fix every finding.

## 5. Release

- [x] 5.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.367` to `0.6.368`.
- [x] 5.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and `python3 -m unittest discover -s
      evals/tests`; grep the output for `OK` and fix anything that fails.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 101 | 46.8k |
| SubagentHandback | 6 | 6.7k |
| Agent | 5 | 3.8k |
| (no tool) | 0 | 1.1k |
| ToolSearch | 2 | 863 |
| Read | 5 | 711 |
| SendMessage | 1 | 476 |
| Monitor | 1 | 293 |
| **Total** | 121 | 60.8k |
