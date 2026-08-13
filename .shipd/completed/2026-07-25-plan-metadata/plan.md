# plan-metadata
Status: verified

## Idea

The planning pipeline is one-size-fits-all: every change gets the same rigor
and the artifacts can express nothing about a change beyond its status. There
is no way to mark a change as lighter-weight, group changes under an epic,
link work to a strategic initiative, or tag it with a cross-cutting theme —
so epics, initiatives, and themes cannot become first-class shipd features:
the format has no place to hold them.

This change lays the format foundation the whole hierarchy
(Initiative → Epic → Change, with Theme orthogonal) hangs on:

- An optional **header metadata block** in `plan.md` — contiguous `Key: value`
  lines immediately after `Status:` — with four recognized keys: `Profile`,
  `Epic`, `Initiative`, `Theme`.
- A **`Profile:`** value (`full` | `lite`, default `full`) expressing rigor.
  Per the decided direction, `lite` relaxes content expectations only — the
  artifact set and structural lint rules are identical for both profiles.
- The **initiative-through-epic rule**: a change carrying `Epic:` must not
  carry `Initiative:` (it derives its initiative through the epic); only a
  standalone change may carry `Initiative:` directly.
- A reserved **`am/config.json`** (stdlib JSON) holding `valid_themes`, so
  theme vocabulary is validated when declared and permissive when absent.
- Lint validation of all of the above, metadata-preserving status writes, and
  documentation in `am/README.md` plus plan-emission guidance.

### Non-goals

- No epic layer yet: no `am/epics/` layout, no `/s:epic` skill, no validation
  that an `Epic:` value names an existing epic — that is the next change.
- No workspace or project machinery: no workspace discovery, no initiative
  briefs, no `projects`/`context.md` — a follow-up change (see Roadmap).
- No structural `lite` relaxation: every change keeps `plan.md`, delta specs,
  and `tasks.md` regardless of profile (explicit user decision).
- No behavior keyed on metadata beyond validation and display — no reporting,
  slicing, or sync.

Affected capabilities: `shipd-spec-format`, `shipd-spec-lint`, `spec-status`,
`shipd-plan` (all modified via ADDED requirements). Impact:
`plugins/s/skills/build/scripts/{spec_common,spec_lint,spec_status}.py` and
their tests, `am/README.md`, `am/config.json` (new),
`plugins/s/skills/plan/references/emission.md`. No new dependencies.

## Implementation

- **Metadata as header lines, not a sidecar file.** Metadata lives as
  `Key: value` lines in the `plan.md` header, matching the existing `Status:`
  pattern. Rejected: a `.yaml`/`.json` sidecar per change — YAML is not
  stdlib-parseable (constitution: engine is stdlib-only Python 3), and a
  sidecar hides the metadata from the document a human reads.
- **Block grammar.** The metadata block is the contiguous run of
  `<Key>: <value>` lines immediately following the `Status:` line, ended by
  the first blank line or heading. Recognized keys: `Profile`, `Epic`,
  `Initiative`, `Theme`. Values are kebab-case slugs (`Profile` restricted to
  `full` | `lite`). Unrecognized keys in the block are lint errors — typo
  safety (`Them: reliability` must not pass silently). A plan with no
  metadata block lints exactly as today, so all existing changes stay valid.
- **Parser location.** `spec_common.py` gains `parse_plan_metadata(text)`
  returning the ordered key→value pairs plus module constants
  `METADATA_KEYS = ("Profile", "Epic", "Initiative", "Theme")` and
  `PROFILES = ("full", "lite")`; `spec_lint.py` gains `check_plan_metadata`
  wired into `lint_change` beside `check_plan_header`. Rejected: parsing
  inline in the linter — `spec_status.py` and future epic tooling need the
  same parse.
- **Exclusivity at lint time.** `Epic:` and `Initiative:` on the same plan is
  a lint error (initiative derives through the epic; only standalone changes
  carry it directly). Enforcing at lint mirrors the source design's CLI
  refusal without needing a CLI verb.
- **Config file.** `am/config.json` is reserved repo config, parsed with the
  stdlib `json` module via `load_config(root)` in `spec_common.py`. When it
  exists and holds a non-empty `valid_themes` array, a `Theme:` value outside
  it is a lint error; when the file is absent or has no `valid_themes`, any
  kebab-case theme passes. A file that exists but is not valid JSON is a lint
  error naming the file. Rejected: a vocabulary section in `constitution.md`
  — that file is prose steering, not machine-parsed config.
- **Status CLI.** `set_status`/`sync` already rewrite only the `Status:` line;
  a test pins that metadata lines survive byte-for-byte, and `show` prints
  recognized metadata lines when present.
- **Risks.** Statusline greps the plan header for `Status:`; metadata sits
  *after* that line so the first-five-non-blank-lines rule and the statusline
  are untouched — guarded by running the full test suite (incl.
  `test_statusline.py`) in the verification barrier. Backward compatibility:
  every new rule fires only when a metadata block is present.

## Roadmap

Follow-up changes, in order (recorded here so the decomposition survives;
each gets its own plan when it starts):

1. **epic-layer** — `am/epics/<slug>/epic.md` (header with `Status:` /
   `Theme:` / `Initiative:` metadata, Decisions and Design sections, change
   stubs with a per-change complexity table), an `/s:epic` skill, lint
   validation that a change's `Epic:` names an existing epic, and epic status
   derived from member changes.
2. **workspace-projects** — workspace discovery (marker file at the workspace
   root), initiative briefs at `<workspace-root>/initiatives/<slug>/brief.md`,
   and **projects** as the grouping layer: a workspace *contains* projects,
   each project groups repos and carries a `context.md` used to focus
   planning; a workspace with no declared projects behaves as one implicit
   project. Whether an initiative can be scoped to a project is decided in
   that change's planning.
3. **theme-tooling** — set-theme convenience and theme/initiative slicing in
   reporting.
