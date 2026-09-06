## 1. The rubric document

- [x] 1.1 [req: knowledge-capture-rubric] Create
      `plugins/s/skills/epic/references/capture-rubric.md` (new directory),
      titled `# Knowledge capture rubric — where arriving information
      belongs`, structured like
      `plugins/s/skills/ask/references/capture-rubric.md`: the four tier
      definitions (binding / reference / durable / noise) with the
      destinations fixed in `plan.md`'s `## Implementation` — including the
      epic-scope amendment discipline (fresh `epic-amend-<slug>` worktree,
      dated provenance line, lint-gated auto-merging PR; never a free epic
      edit) and the durable tier's explicit handoff to the capture
      durability rubric at
      `plugins/s/skills/ask/references/capture-rubric.md` without restating
      its three tiers — then a calibrated examples table (>= 8 rows, >= 2
      per tier, each with a one-line rationale, covering the categories the
      plan names), then the four tie-breakers. Call it the "knowledge
      capture rubric" throughout; reference no unshipped verb, flag, or
      skill argument.

## 2. Consult wiring

- [x] 2.1 [P2] [req: plan-rubric-consult] In
      `plugins/s/skills/plan/SKILL.md`: add a "Classify what arrived"
      bullet beside the existing "Capture the typed resolution back into
      the queue" bullet (lines 594-637) — each folded-in typed answer is
      classified against the knowledge capture rubric
      (`${CLAUDE_PLUGIN_ROOT}/skills/epic/references/capture-rubric.md`)
      into exactly one tier, naming all four destinations (epic-scope
      binding information is flagged for the epic's amendment discipline,
      never a free epic edit) and deferring durable-tier queue mechanics to
      the existing oracle-queue capture rule unchanged. At the "Supplied
      documents" rule (~line 298), add one sentence identifying the
      install-and-link path as the rubric's reference tier. In
      `plugins/s/harness/bodies/plan.md` step 4, add one compact consult
      sentence naming the four tiers and
      `"$S/../../epic/references/capture-rubric.md"`; keep the rendered
      body under 120 lines (currently 88).
- [x] 2.2 [P2] [req: build-qa-rubric-consult] In
      `plugins/s/skills/build/SKILL.md` Phase 4 (lines 376-394): add the
      consult — classify what a sub-agent answer or mid-build user
      interjection carries against the knowledge capture rubric by its
      `${CLAUDE_PLUGIN_ROOT}` path; binding at change scope stays
      "update the spec artifacts first" (name it as the binding tier),
      binding at epic scope is surfaced to the user for the amendment
      discipline, reference installs via the docs kind and links the epic's
      `## References`, durable routes to the wiki/queue, noise is recorded
      nowhere. In `plugins/s/harness/bodies/build.md`, add one compact
      consult sentence naming the four tiers and
      `"$S/../../epic/references/capture-rubric.md"`, placed in step 5's
      common text (outside the `if:subagents` gates) so both renderings
      carry it; keep both rendered bodies under 120 lines (currently 98
      with all features).
- [x] 2.3 [P2] [req: epic-authoring-rubric-consult] In
      `plugins/s/skills/epic/SKILL.md`: at the question-contract fold-in
      ("Ask once, then converge", lines 123-137, or flow step 2), add the
      consult — classify each folded-in answer against the knowledge
      capture rubric by its `${CLAUDE_PLUGIN_ROOT}` path; binding lands in
      the `## Decisions` section being authored, reference installs and
      links from `## References`, durable routes to the wiki/queue, noise
      is dropped. In `plugins/s/harness/bodies/epic.md` section 3, add one
      compact consult sentence naming the four tiers and
      `"$S/../../epic/references/capture-rubric.md"`; keep the rendered
      body under 120 lines (currently 97).

## 3. Ship gate

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.6.181 -> 0.6.182. Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (all pass, no textual installed) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py --epic
      epic-knowledge --root .` (exit 0). Verify the rendered harness bodies
      stay under 120 lines via the existing harness tests.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 132 | 22.3k |
| Edit | 9 | 5.3k |
| Read | 34 | 2.8k |
| Agent | 4 | 1.4k |
| SendMessage | 3 | 1.3k |
| ToolSearch | 4 | 599 |
| (no tool) | 0 | 520 |
| Monitor | 2 | 33 |
| Write | 1 | 3 |
| **Total** | 189 | 34.3k |
