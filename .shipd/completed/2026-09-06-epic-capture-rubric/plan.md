# epic-capture-rubric
Status: verified
Epic: epic-knowledge

## Idea

Ship the knowledge capture rubric — the four-tier reference document
(binding / reference / durable / noise) that tells every skill where
arriving information belongs — plus consult wiring in the plan, build, and
epic skills at their information-arrival moments.

### Motivation

Since the `docs` kind and the `## References` shelf shipped, knowledge
arriving mid-plan, mid-build, or mid-authoring has four possible homes —
the change's binding artifacts, the epic's reference shelf, the durable
wiki, or deliberately nowhere — but no skill names the routing, so typed
decisions still land wherever the session improvises and are lost to the
next one (epic `epic-knowledge`).

### Details

- One reference document, modeled on `ask`'s capture durability rubric
  (tiers, calibrated examples table, tie-breakers), at
  `plugins/s/skills/epic/references/capture-rubric.md`.
- Consult wiring at three arrival moments: plan's question rounds and
  supplied-document intake, build's Q&A loop, epic authoring's answer
  fold-in — each naming the rubric by plugin-root path, with compact
  mirrors in the harness plan/build/epic bodies.
- The rubric classifies; humans and skills still decide. No engine code.

Affected capabilities: `shipd-epic`, `shipd-plan`,
`build-subagent-handoff` (all extended). Impact:
`plugins/s/skills/epic/references/capture-rubric.md` (new),
`plugins/s/skills/plan/SKILL.md`, `plugins/s/skills/build/SKILL.md`,
`plugins/s/skills/epic/SKILL.md`, `plugins/s/harness/bodies/plan.md`,
`plugins/s/harness/bodies/build.md`, `plugins/s/harness/bodies/epic.md`,
`plugins/s/.claude-plugin/plugin.json` (version bump).

### Non-goals

- No amendment flow or `epic-amend-check` guard verb — sibling
  `epic-amend-flow`. The rubric describes the amendment *discipline* (fresh
  `epic-amend-<slug>` worktree, dated provenance, lint-gated PR) without
  referencing any unshipped verb or skill argument.
- No repo-local wiki fallback — sibling `repo-wiki-fallback`. The durable
  tier routes to the workspace wiki and queue as they exist today, and the
  rubric promises nothing about bare repos.
- No change to `ask`'s capture durability rubric
  (`plugins/s/skills/ask/references/capture-rubric.md`) or its wiring: it
  remains the sub-classifier for the durable tier's queue writes.
- No automatic capture and no new engine verbs, lint checks, or automated
  tests — the deliverable is one reference document plus skill-text wiring,
  validated by inspection scenarios exactly as `shipd-ask`'s
  `capture-rubric` requirement is.
- No migration of existing skill prose beyond the named consult moments.

## Implementation

- **One canonical rubric file:**
  `plugins/s/skills/epic/references/capture-rubric.md` (the `epic` skill
  gains its first `references/` directory). Document title:
  `# Knowledge capture rubric — where arriving information belongs`. Prose
  name everywhere — in the rubric, the three SKILL.md wirings, and the
  harness bodies — is **"knowledge capture rubric"**, never bare "capture
  rubric", so it can never be confused with `ask`'s capture *durability*
  rubric when both appear in the same skill.
- **Structure mirrors `ask`'s rubric:** tier definitions first, then a
  calibrated examples table, then tie-breakers. Four tiers, exactly one per
  item of arriving information:
  1. **Binding** — changes what executors do. At change scope it lands in
     the change's own artifacts (`plan.md`'s `## Implementation` or
     `## Questions and answers` ledger, delta specs). At epic scope the
     epic's `## Decisions` change **only** through the sanctioned amendment
     discipline — a fresh `epic-amend-<slug>` worktree, the amended Decision
     stamped with a dated provenance line, lint-gated, shipped as an
     auto-merging PR, mirroring the epic-close derivation — never a free
     edit of the epic file.
  2. **Reference** — supports this feature but does not bind executors: a
     strategy memo, meeting notes, an API excerpt. Installed through the
     emit engine (`spec_emit.py docs <slug> --from <file>` for arbitrary
     documents; research and video keep their own kinds) and linked from
     the epic's `## References` shelf — or cited in `plan.md` prose when
     the change has no resolving epic.
  3. **Durable** — outlives the feature: standing engineering positions,
     conventions, workspace facts. Routes to the workspace wiki via
     `/s:teach` or the oracle queue (`wiki-queue-*`), where the capture
     durability rubric (`plugins/s/skills/ask/references/capture-rubric.md`)
     then governs whether and how the queue write happens. The rubric names
     this handoff explicitly and does not duplicate the three durability
     tiers.
  4. **Noise** — session logistics, vented frustration, exploratory
     tangents: recorded nowhere, deliberately. The plan's Q&A ledger may
     still record a resolution for the change itself; noise means no
     *knowledge* capture.
- **Calibrated examples table** with at least eight rows and at least two
  per tier, each row example / tier / one-line rationale, covering at
  least: a mid-delivery scope cut and an executor-facing constraint
  (binding); a pasted strategy memo and an API excerpt (reference); a
  standing engineering position and a cross-feature convention (durable);
  a scheduling remark and a vented complaint (noise).
- **Tie-breakers**, at least these four leans: obeyed-vs-consulted decides
  binding vs reference; tied-to-this-feature's-lifetime vs outliving-it
  decides reference vs durable; a borderline case leans toward the
  less-capturing, less-binding tier (matching `ask`'s lean); and scope
  decides the binding tier's home — member plan at change scope, epic
  Decisions via the amendment discipline at epic scope.
- **Plugin-skill wiring references the rubric by plugin-root path**, exactly
  as `plan/SKILL.md:599` references `ask`'s today:
  `${CLAUDE_PLUGIN_ROOT}/skills/epic/references/capture-rubric.md`.
  - `plugins/s/skills/plan/SKILL.md`: one consult rule where typed answers
    fold in (the oracle-consultation bullet list around lines 594–637,
    beside the existing "Capture the typed resolution back into the queue"
    bullet, which stays authoritative for its oracle-queue case) and one
    sentence at the supplied-documents rule (~line 298) noting the install
    path is the rubric's reference tier.
  - `plugins/s/skills/build/SKILL.md`: Phase 4 (Q&A loop, lines 376–394)
    gains the consult — classify what an answer or a mid-build user
    interjection carries; binding → update the spec artifacts first
    (already the rule, now named as the rubric's binding tier; epic-scope
    binding information is surfaced to the user for the amendment
    discipline, never a free epic edit), reference → docs kind + shelf,
    durable → wiki/queue, noise → nothing.
  - `plugins/s/skills/epic/SKILL.md`: the answer fold-in (flow step 2 /
    question contract, lines 104–137) gains the consult — during authoring
    the binding tier's home is the `## Decisions` section being written (no
    amendment needed for an unborn epic), reference → `## References`,
    durable → wiki/queue, noise → dropped.
- **Harness wiring points at the one canonical file, no inlined copies.**
  Each of `plugins/s/harness/bodies/plan.md` (step 4), `bodies/build.md`
  (step 5's common text, outside the `if:subagents` gates, so both
  renderings carry it), and `bodies/epic.md` (section 3) gains a compact
  consult sentence naming the four tiers and the path
  `"$S/../../epic/references/capture-rubric.md"` — the `$S/../..`
  sibling-skill path precedent of `bodies/gate.md:52`. Rendered bodies stay
  under the 120-line budget (currently plan 88 / build 98 / epic 97);
  `plugins/s/harness/references/{plan,build,epic}.md` are touched only if a
  body sentence needs relocating to stay in budget. No change to
  `harness/references/ask.md` or the ask body.
- **Ship gate:** bump `plugins/s/.claude-plugin/plugin.json` `0.6.181` →
  `0.6.182`; the stdlib-only suite
  (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
  `spec_lint.py --epic epic-knowledge` must pass. No new automated tests:
  the delta scenarios are inspection-based, matching the precedent of
  `shipd-ask`'s `capture-rubric` requirement.
