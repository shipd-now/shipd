# codebase-first-shared
Status: verified
Planned-at: c938fcbcfabf09ae41549d7e931f720b87f451d4
Gated-hash: b8dc6bd5d263

## Idea

Hold the codebase-first rule once, in the shared headless reference, and move `/s:plan`'s enrichment mode into its own reference.

### Motivation

The codebase-first rule is restated in three places: the headless reference's thin `## Codebase first`, `/s:plan`, and `/s:epic`. An external harness that loads only the headless reference gets the weakest wording. Enrichment mode also sits inline in `plan/SKILL.md`, though only a rejected change needs it.

### Details

- Replace the body of `## Codebase first` in `plugins/s/skills/ask/references/headless.md` with the engine-neutral rule, and say it binds interactive sessions too and that `/s:plan` loads it.
- Reduce the `## Codebase-first rule (non-negotiable)` bodies of `plan/SKILL.md` and `epic/SKILL.md` to the one-liner, a pointer, and the interactive application.
- Move the enrichment loop and its re-gate exit from `plan/SKILL.md` into `plugins/s/skills/plan/references/enrichment.md`, leaving the `locate` branch and a pointer.
- Pin the new text and the new file in `test_external_loaders.py`. Bump the plugin version.

Affected capabilities: `shipd-ask` (modified) and `shipd-plan` (modified and extended).

### Non-goals

- No change to the other three headless headings, the manifest, or the prd skill.
- No change to the enrichment procedure itself. It moves verbatim, apart from paths and pointers.

## Implementation

- **One rule, three readers.** `## Codebase first` is the single source. The two skills keep their heading, because other text refers to it by name, and add only their interactive application.
- **Pure move.** The enrichment text keeps its wording. Headings drop one level, and two references to `SKILL.md` sections gain a path.

Risk: a loader that reads the old, shorter body. The manifest lists the heading only, and the heading is unchanged.

## Readiness attestation

### Problem and motivation

The rule is restated in three places with different strength, and rarely-used enrichment text loads on every `/s:plan` run.

Evidence:

- `plugins/s/skills/ask/references/headless.md` holds a three-sentence `## Codebase first`; `plan/SKILL.md` and `epic/SKILL.md` each hold a longer copy.
- `plan/SKILL.md` carries about sixty lines of enrichment procedure.

### Scope and non-goals

Only the headless reference, the plan and epic skills, one new plan reference, a test file, and the plugin version change.

Evidence:

- In scope: `headless.md`, `plan/SKILL.md`, `epic/SKILL.md`, `plan/references/enrichment.md`, `test_external_loaders.py`, `plugin.json`.
- Out of scope: the manifest, `prd/SKILL.md`, the gate, the enrichment procedure's content.

### Affected capabilities and files

`shipd-ask` modifies `headless-contract-reference`, and `shipd-plan` modifies `codebase-first-investigation` and gains one requirement.

Evidence:

- Base hash from `spec_status.py base-hash shipd-ask headless-contract-reference`: b9ba2c93921e.
- Base hash from `spec_status.py base-hash shipd-plan codebase-first-investigation`: a86bb7d1e772.

### No open task-shaping decision

The request fixes the wording, the headings that stay, and the file that holds enrichment.

Evidence:

- The request names each file, the kept headings, and the move's verbatim rule.
