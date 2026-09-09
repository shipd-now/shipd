# epic-prd-link
Status: verified
Epic: prd-discovery

## Idea

Let an epic carry an optional `PRD: <slug>` metadata line — recognized by the
epic linter, required to resolve across the workspace chain, and reported by
`epic-show` — closing the hierarchy Initiative → PRD → Epic → Change.

### Motivation

The epic mandates that discover-phase output feed decomposition via an
optional `PRD:` line on epics, but the epic metadata registry rejects any key
beyond `Theme:` and `Initiative:`, so a PRD cannot yet be cited by the epics
built from it.

### Details

- `EPIC_METADATA_KEYS` gains `PRD`; the epic linter resolves the value across
  the workspace chain; `epic-show` reports the line via the existing generic
  metadata rendering.
- Every surface enumerating the epic metadata keys is updated: the format
  README, the `/s:epic` skill contract, and the harness fallback reference.

Affected capabilities: `shipd-spec-format` (modified `epic-header-metadata`).
Impact: `plugins/s/skills/build/scripts/spec_common.py`,
`plugins/s/skills/build/scripts/spec_lint.py`, `.shipd/README.md`,
`plugins/s/skills/epic/SKILL.md`, `plugins/s/harness/references/epic.md`,
tests `test_spec_common.py`/`test_spec_lint.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies.

### Non-goals

- No `epic-set-prd` guarded verb — a new epic writes the line at authoring
  time; a live epic gains one only through a deliberate future change.
- No PRD-side back-links: a PRD never lists its epics.
- No `epic-show` code changes beyond what the key registry provides — the
  metadata rendering is already generic.
- No change to plan-level metadata (`Profile`/`Epic`/`Initiative`/`Theme`
  on changes are untouched).

## Implementation

- **Key registry.** `spec_common.py:87`: `EPIC_METADATA_KEYS` becomes
  `("Theme", "Initiative", "PRD")`. That one tuple drives
  `_check_epic_metadata`'s recognition and kebab checks (`spec_lint.py:515`)
  and `_epic_metadata`'s epic-show filtering (`spec_status.py:1301`) — no
  other recognition code exists. The value is the PRD's kebab slug.
- **Resolution check.** New `check_prd_reference(root, pairs, errors)` in
  `spec_lint.py` beside `check_initiative_reference` (`spec_lint.py:747`),
  same shape: find the `PRD` pair (nothing to do when absent), resolve with
  `sc.resolve_prd(root, value)`, and on `None` append a `LintError` naming
  the expected path (`sc.prd_path(ws_root, value)` where a workspace
  resolves; when no workspace is discoverable the check is skipped silently,
  exactly `check_initiative_reference`'s CI-safe rule — a bare CI checkout
  must lint clean without depending on files outside the repository).
  Called from `lint_epic` directly after `check_initiative_reference`
  (`spec_lint.py:707`). Rejected: a warn-only check — a dead discover link
  is exactly the drift the linter exists to stop.
- **Documentation surfaces** (each currently says "only Theme and
  Initiative"): `.shipd/README.md:753` metadata paragraph;
  `plugins/s/skills/epic/SKILL.md:375` (the epic contract bullet) plus its
  emission template's optional header lines; and
  `plugins/s/harness/references/epic.md:8-9` (template header) and `:53`
  (contract sentence) — each gains the optional
  `PRD: <kebab-prd>` line with a one-phrase note that it must resolve to a
  workspace PRD.
- **Tests.** `test_spec_common.py`: the tuple's new shape.
  `test_spec_lint.py`: an epic carrying a resolving `PRD:` lints clean (temp
  workspace hosting the PRD); an unresolvable `PRD:` errors naming the
  expected path; a non-kebab value errors; an epic with no `PRD:` line is
  untouched (regression); `Profile:` stays rejected. An `epic-show` case in
  `test_spec_status.py` asserting the metadata line renders.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next free
  patch at build time (0.6.196 if main still sits at 0.6.195).
- **Risk**: an existing epic in some repo could already carry a stray `PRD:`
  key that was previously *rejected* — recognition can only turn an error
  into acceptance-with-resolution, never the reverse, so no currently-clean
  epic can start failing except by carrying a dangling `PRD:` value, which
  was an unrecognized-key error before. Net: no lint regressions possible.
