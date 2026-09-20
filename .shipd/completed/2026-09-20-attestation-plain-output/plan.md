# attestation-plain-output

Status: verified

## Idea

Replace the readiness attestation's terminal format — a markdown table with
fully-cited evidence cells — with a plain-language summary, and move the full
evidence into the emitted `plan.md`.

### Motivation

The evidence-laden table renders as an unreadable stacked wall in real
terminals (long cells defeat tabular rendering), defeating the attestation's
own scanned-at-a-glance goal. The user asked for plain statements in the
terminal, with the detail preserved in the spec file and the output naming
that file's full path.

### Details

- The printed attestation becomes four plain-language headed statements — one
  per checklist item, stating counts and reasons rather than citations — plus
  one closing line naming the absolute path of the emitted `plan.md` that
  carries the full evidence.
- The emitted `plan.md` gains a `## Readiness attestation` section: per item,
  the plain statement first, then the evidence dot-points to the existing
  citation standards (unchanged in substance, runnable-premise observations
  included).
- Surfaces updated: `plugins/s/skills/plan/references/readiness.md`,
  `plugins/s/skills/plan/references/emission.md`,
  `plugins/s/skills/plan/SKILL.md`, `plugins/s/harness/bodies/plan.md`,
  `plugins/s/harness/references/plan.md`, the `shipd-plan` capability, and the
  plugin version.

### Non-goals

- No linter change: `spec_lint.py` keeps requiring only `## Idea` and
  `## Implementation`. Making the new section lint-required would fail every
  already-installed plan and eval fixture on later validate runs, so the
  section is enforced by the skill's self-review instead.
- No change to the four checklist items, the evidence citation standards, the
  runnable-premise rule's substance, or the context gate (`spec_gate.py`).
- No change to the enrichment loop, the QA ledger, or the depth gate.

## Implementation

Binding decisions:

- **Printed shape.** Four entries, each `**<item name>** — <one or two plain
  sentences>`, in checklist order; then one closing line
  `Full evidence: <absolute path to plan.md>`. No table, no citations, no
  command output in the terminal.
- **Section shape.** `## Readiness attestation` placed after
  `## Implementation` (and after `## Questions and answers` when that section
  exists), holding one level-3 subsection per checklist item
  (`### Problem and motivation`, `### Scope and non-goals`,
  `### Affected capabilities and files`,
  `### No open task-shaping decision`), each a plain statement paragraph
  followed by an `Evidence:` dot-point list to the unchanged citation
  standards. Runnable-premise invocations and observed outputs land under the
  third subsection's evidence.
- **Ordering preserved.** Evidence is still assembled before authoring; the
  change name is resolved (per `emission.md`'s naming rule) before the
  attestation prints, so the closing line names the real destination path —
  inside a worktree that is
  `<repo-root>/.worktrees/<change>/.shipd/planned/<change>/plan.md`.
- **Marker safety.** The section's phrasing must avoid the context gate's
  placeholder markers (`spec_gate.py`'s `PLACEHOLDER_WORDS` tuple and its
  triple-question-mark marker), the
  same caution the QA ledger already carries.
- **Self-review check.** The self-review pass verifies every attestation item
  in the staged `plan.md` carries evidence dot-points; an item without them is
  unmet and blocks installation.
- **Harness mirrors.** `plugins/s/harness/bodies/plan.md` and
  `plugins/s/harness/references/plan.md` state the same contract compactly;
  neither may keep the table mandate.
- **Version bump.** `plugins/s/.claude-plugin/plugin.json` bumps in the same
  change (cache-snapshot rule in `AGENTS.md`).

## Readiness attestation

### Problem and motivation

The attestation table is unreadable in real terminals, and the user asked for
plain statements backed by detail saved in the spec.

Evidence:

- `plugins/s/skills/plan/references/readiness.md:63-73` mandates the markdown
  table whose long evidence cells stack into the reported wall of text.
- The request pins the design: simple above details in the spec, only the
  simple form printed, with the file's full path named in the output.

### Scope and non-goals

The change touches only the attestation's format surfaces; the checklist,
linter, and gate logic stay untouched.

Evidence:

- In scope: `readiness.md:55-103`, `emission.md:106-110` area,
  `SKILL.md:395-400`, `harness/bodies/plan.md:53`,
  `harness/references/plan.md:8-11`, `shipd-plan` capability, plugin version.
- Out of scope: `spec_lint.py:71` (`REQUIRED_PLAN_SECTIONS`) and
  `spec_gate.py` are not edited.

### Affected capabilities and files

Six prose surfaces and the version manifest are affected because each restates
the attestation's format; one capability is modified.

Evidence:

- Capability `shipd-plan`: requirements `readiness-attestation`
  (base 4a061d476072) and `premise-evidence-in-attestation`
  (base c2f65fd0b6a5), both hashes from `spec_status.py base-hash`.
- Files: the six paths listed under scope plus
  `plugins/s/.claude-plugin/plugin.json`.
- Runnable premises, all executed: `spec_status.py pipeline-show --json` →
  exit 0, `source: default`; `wiki-show --personal` → exit 1 (no store, skip
  is silent); `related readiness attestation …` → `shipd-plan` score 202;
  `base-hash` → the two hashes above; `shipd worktree attestation-plain-output`
  → worktree created, branch `change/attestation-plain-output`.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Core design (simple printed form, details in the spec, path in the output):
  settled by the user in the request.
- Linter scope (no lint-required section): settled by investigation —
  `spec_lint.py:326` fails any plan missing a required section, which would
  break already-installed plans and eval fixtures.
- Section name, placement, and printed markdown shape: settled by the planner
  following the QA-ledger precedent in `emission.md:192-235`.
