# prd-store
Status: verified
Epic: prd-discovery

## Idea

Add the engine foundation for PRDs: workspace-level path helpers, the header
grammar and status vocabulary, the additive three-tier required-section
registry, and a `lint_prd` validator with a `--prd` CLI mode.

### Motivation

The `prd-discovery` epic makes the PRD the discover phase's artifact, but the
engine has no PRD grammar, paths, or validation at all; the emit verb, the
templates, and the `/s:prd` skill all build on this store foundation.

### Details

- `spec_common.py`: PRD constants (statuses, tiers, tier-section registry,
  metadata keys) and path/resolution helpers mirroring the initiative-brief
  block.
- `spec_lint.py`: `lint_prd` validating a single PRD against the grammar and
  its tier's section contract, plus a `--prd <slug>` CLI mode mirroring
  `--initiative`.
- New `shipd-prd` capability; one ADDED `prd-lint-mode` requirement in
  `shipd-spec-lint`.

Affected capabilities: `shipd-prd` (added), `shipd-spec-lint` (added
requirement). Impact: `plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/scripts/spec_lint.py`,
`plugins/s/skills/build/tests/test_spec_common.py`,
`plugins/s/skills/build/tests/test_spec_lint.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies.

### Non-goals

- No emit/read verbs (`spec_emit.py prd`, `cat prd`) — the `prd-emit` member.
- No template files under the prd skill — the `prd-templates` member (its
  drift-guard test against this registry lands there too).
- No `PRD:` epic metadata line — the `epic-prd-link` member.
- No `/s:prd` skill and no search-surface addition for PRDs.

## Implementation

- **Constants in `spec_common.py`**, in a new PRD block beside the
  workspace-content block (`spec_common.py:1267`):
  - `PRD_STATUSES = ("draft", "approved", "superseded")` — a PRD is a
    document, not a change; deliberately not the five change statuses.
  - `PRD_TEMPLATE_TIERS = ("basic", "standard", "comprehensive")`.
  - `PRD_TIER_SECTIONS` mapping each tier to its full required level-2
    section tuple, additively nested (settled in Q1):
    `basic` → `("## Problem", "## Solution", "## Success criteria")`;
    `standard` → basic + `("## Users", "## Requirements", "## Non-goals")`;
    `comprehensive` → standard + `("## Risks", "## Rollout",
    "## Open questions")`. Each tier's tuple is complete (not just the
    increment), so the linter does one membership walk. Rejected:
    increment-only tuples — every consumer would re-derive the union.
  - `PRD_METADATA_KEYS = ("Initiative",)` — the only recognized header
    metadata key, mirroring `BRIEF_METADATA_KEYS`.
- **Path helpers in `spec_common.py`**: `prds_dir(ws_root)` →
  `<content-dir>/prds`, `prd_path(ws_root, slug)` →
  `prds_dir/<slug>/prd.md`, and `resolve_prd(start, slug)` walking the
  workspace chain exactly as `resolve_initiative_brief` does (nearest chain
  member hosting the file wins; `None` when nothing resolves).
- **Header grammar** (enforced by `lint_prd`): line 1 is `# <slug>` matching
  the directory; a `Status:` line among the first five non-blank lines with a
  value in `PRD_STATUSES`; a `Template:` line among the first five non-blank
  lines with a value in `PRD_TEMPLATE_TIERS` — **mandatory**, because the
  artifact contract is explicit ("standard is the default" is the authoring
  skill's behavior, not lint leniency; rejected: defaulting an absent line);
  optional `Initiative: <kebab>` metadata validated against
  `PRD_METADATA_KEYS`, with an `Initiative:` value additionally required to
  resolve through `resolve_initiative_brief` (an unresolvable initiative is
  an error, mirroring `check_initiative_reference`'s strictness).
- **Section contract**: every section named by the PRD's tier in
  `PRD_TIER_SECTIONS` must be present as an exact level-2 heading line;
  extra sections are allowed (the registry is a floor, not a ceiling), so a
  comprehensive PRD stays valid when the interview adds bespoke sections.
- **`lint_prd(ws_root, slug, errors)` in `spec_lint.py`**, placed beside
  `lint_initiative` (`spec_lint.py:805`), appending one `LintError` per
  violation with the PRD path, following `lint_initiative`'s structure
  (missing-file short-circuit, title, status, metadata loop, section walk).
- **CLI mode**: `--prd <slug>` in `spec_lint.py`'s parser and dispatch,
  mirroring `--initiative` (`spec_lint.py:1526-1536`): resolve
  `sc.find_workspace_root(args.root)`; when `None`, the observed error shape
  (`no workspace found from <abs-root>; --prd requires a discoverable
  workspace root`, exit 1); else `lint_prd`. `--json` output comes free from
  the existing shared rendering.
- **Tests**: `test_spec_common.py` covers the constants' shapes (additive
  nesting asserted programmatically), path helpers, and `resolve_prd` chain
  behavior; `test_spec_lint.py` covers a conforming PRD per tier, each
  grammar violation (title, status, missing/unknown Template, unknown
  metadata key, unresolvable Initiative, missing tier section), the
  extra-sections allowance, and the no-workspace CLI error.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` `0.6.189` →
  `0.6.190`.
- **Risk**: section matching is exact-line (`## Problem`), so a future
  template with trailing decoration would fail lint — deliberate strictness;
  the `prd-templates` drift-guard will keep skeletons aligned.

## Questions and answers

### Q1: Which per-tier required-section lists does the registry pin?
- **Question:** The tier registry needs concrete section lists the linter
  enforces and the templates/interview follow. Options: (a) additive
  supersets in house style — basic: Problem, Solution, Success criteria;
  standard adds Users, Requirements, Non-goals; comprehensive adds Risks,
  Rollout, Open questions; (b) additive with corporate names
  (Background/Objectives/KPIs style); (c) independent per-tier lists.
  Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a) — additive supersets in house style. Nesting keeps
  mid-interview tier escalation monotone (already-answered sections stay
  valid) and the names match the why-first house style (Problem before
  Solution, explicit Non-goals mirroring plan.md and epics).
- **Queued:** q-prd-tier-section-registry
