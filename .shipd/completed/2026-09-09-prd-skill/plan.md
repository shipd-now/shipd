# prd-skill
Status: verified
Epic: prd-discovery

## Idea

Ship the `/s:prd` skill: a multi-round, tier-aware PRD interview that
investigates first, grills the user section by section against the active
template, and installs the result through the engine's staged `prd` emit —
plus the harness body and fallback reference that make the command portable.

### Motivation

The whole PRD substrate — store, templates, emit/read paths, search, epic
linkage — is shipped, but the discover-phase front door does not exist: no
skill runs the interview the `prd-discovery` epic was created to deliver.

### Details

- New `plugins/s/skills/prd/SKILL.md` — the interview contract below.
- New `plugins/s/harness/bodies/prd.md` (+ `plugins/s/harness/references/prd.md`,
  required by its feature gates), re-entering the bodies 1:1 guard.
- `AGENTS.md`'s `/s:` skill enumeration gains `/s:prd`.

Affected capabilities: `shipd-prd` (added requirement). Impact: the three new
markdown files, `AGENTS.md`, `plugins/s/.claude-plugin/plugin.json` (version
bump). No engine-script changes, no new dependencies.

### Non-goals

- No new engine verbs — approval is a re-install with `Status: approved`
  through the existing `spec_emit.py prd --replace`; no status CLI change.
- No extra files under `plugins/s/skills/prd/references/` — the templates
  drift guard pins that directory to exactly the three tier skeletons, so
  all interview guidance lives in `SKILL.md`.
- No documentation-site changes — the `prd-doc` member.
- No `/s:epic` changes — its `PRD:` support already shipped.

## Implementation

- **`SKILL.md` contract** (the binding structure; the builder writes the
  prose to sibling quality — `plugins/s/skills/initiative/SKILL.md` and
  `plugins/s/skills/plan/SKILL.md` are the style exemplars):
  1. *Frontmatter*: `name: prd`; description covering "create a PRD",
     "product requirements", "discover phase", "write a PRD for …",
     trigger phrases including `/s:prd`.
  2. *Role*: the PRD interviewer — turn a product idea into a lint-clean
     workspace PRD through interrogation; the discover phase's front door.
  3. *Announce the version first* from
     `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`
     (`shipd:prd v<version>`), matching every sibling.
  4. *Engine paths*: STATUS_CLI (`spec_status.py`), EMIT_CLI
     (`spec_emit.py`), templates at
     `${CLAUDE_PLUGIN_ROOT}/skills/prd/references/<tier>.md`.
  5. *Workspace preflight*: run `STATUS_CLI workspace-show`; when no
     workspace is discoverable, report that PRDs live in the workspace,
     point at `/s:workspace init`, and stop — never fall back to a
     repo-local write.
  6. *Investigate before asking (codebase-first, non-negotiable)*: run
     `shipd search` (or `STATUS_CLI search`) over the idea's terms, read the
     hits — code, specs, wiki pages, initiative briefs, existing PRDs (also
     guarding against a duplicate PRD slug) — and read the workspace roster;
     everything discoverable is investigated, never asked.
  7. *Template selection*: start from `standard`; read the active tier's
     template file; state the tier choice and its reason in one visible
     sentence. Escalate to `comprehensive` when discovered complexity
     warrants (multi-project blast radius, regulatory/risk weight, phased
     rollout, many user classes) or de-escalate to `basic` for a small
     self-contained idea — judged relative to the workspace, announced when
     it happens; the additive registry means answered sections survive an
     escalation and extra answers are simply kept as allowed extra sections
     after a de-escalation.
  8. *The interview — multi-round grilling*: the epic's sanctioned exception
     to the single-batched-round house style. One round per template
     section (2–4 focused questions, concrete options, recommended default
     first, grounded in investigation), until every required section of the
     active tier can be filled with the user's substance — never invented
     filler. AskUserQuestion dialogs are the vehicle where the harness has
     them; plain-text numbered typed rounds otherwise.
  9. *Compose and install*: pick the kebab slug (confirm it in the
     interview's first round); fill the template — title placeholder →
     slug, each italic guidance line replaced wholesale by the section's
     content; add `Initiative: <slug>` only when the user names a parent
     initiative that resolves. Author in a staging file (`mktemp`), install
     with `EMIT_CLI prd <slug> --from <staging>` (never writing the
     workspace path), fix findings and re-run until it installs clean, then
     read it back with `STATUS_CLI cat prd <slug>` as confirmation.
  10. *Ending*: summarize the PRD (slug, tier, sections), state that
      approval is a later re-install with `Status: approved` via
      `--replace`, and point at `/s:epic` on its own line — an epic born
      from this PRD carries `PRD: <slug>`. Stop; the skill never invokes
      `/s:epic` itself.
  11. *Question rejection recovery*: the house-standard section, verbatim in
      spirit.
- **Harness body `bodies/prd.md`**: opens with a
  `<!-- description: … -->` one-liner; distills the flow above router-style;
  gates only on registry features — `question-dialogs` around the
  round-vehicle choice (dialog vs typed round, mirroring
  `bodies/initiative.md:26-31`) and `file-references` around
  `Read {refs}/prd.md` with an author-from-shape fallback (mirroring
  `bodies/initiative.md:36-42`). Because it carries gates,
  **`references/prd.md` is mandatory**: the PRD shape (header grammar,
  status vocabulary, the three tiers' section lists) and the emit-install
  rule, condensed like `references/initiative.md`. The generic
  `test_harness_bodies` suite then covers both files (description marker,
  gate vocabulary, fallback presence, 1:1 guard) with no new tests.
- **Bodies guard re-entry**: adding `SKILL.md` makes `prd` a skill directory
  again, and the body lands in the same change, so
  `test_every_command_has_exactly_one_body_template` passes — closing the
  gap recorded when `prd-templates` shipped.
- **`AGENTS.md`**: the "Spec layout and lifecycle" enumeration gains
  `/s:prd` ("to interview for and install a workspace PRD") in list
  position near `/s:plan`/`/s:epic`.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next free
  patch at build time (0.6.197 if main still sits at 0.6.196).
- **Risk**: skill prose drifting from the engine contracts it names — the
  mitigations are the harness suite's generic checks plus citing only
  shipped verbs (`workspace-show`, `search`, `prd`, `cat prd`), every one
  exercised live in this epic's earlier members.
