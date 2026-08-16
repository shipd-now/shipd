# quickstart-docs
Status: verified
Epic: shipd-dx

## Idea

First-hour documentation: a `docs/quickstart.md` taking a newcomer from
install to their first shipped change, a newcomer-first README ordering, and
a fix for the README capability's stale pre-port branding.

### Motivation

The README is written as a format authority rather than a first hour, and
its governing `project-readme` capability still pins the pre-port
`auto:mikk` banner and `am` plugin naming that the shipped README no longer
uses; the `shipd-dx` epic makes a guided first hour its final success
criterion.

### Details

- New `docs/quickstart.md`: install (one command), `shipd doctor`,
  `/s:onboard` for the guided tour, first `/s:plan` → `/s:build` in the
  reader's own repository, then `shipd board` / `shipd status` to watch it —
  each step with the exact command.
- README restructured newcomer-first: banner → what shipd is in a few
  sentences → install → quickstart link → skills table → the engine
  internals that exist today.
- `project-readme` drift fix: the banner requirement says `shipd` (matching
  the shipped README), and the two requirements naming the `am` plugin say
  the `s` plugin.

Affected capabilities: `project-readme` (modified). Impact: `README.md`,
`docs/quickstart.md` (new). Docs only — no code, no tests (nothing runnable
to test), no plugin version bump (nothing under `plugins/s/` changes).

### Non-goals

- No install or CI section content — `public-install` owns the install-mode
  text and `ci-lint-action` the CI snippet; this member orders and links,
  and builds last so it documents what those members shipped.
- No restating of the requirement/delta grammar — `.shipd/README.md` stays
  the grammar authority (existing requirement, unchanged).
- No per-skill reference pages beyond the skills table — the epic's docs
  scope is the first hour, not a manual.
- No changes to the onboarding skill itself (`/s:onboard` is linked, not
  edited).

## Implementation

- **The drift fix rides this member** because it owns the README's
  requirements: the banner requirement's `auto:mikk` predates the
  `shipd-port` epic and the shipped README already renders `shipd` (the
  spec is wrong, not the file), and two requirements name the `am` plugin
  this repo ships as `s`. Fixing them anywhere else would collide with this
  member's MODIFIED blocks.
- **Quickstart lives in `docs/`** beside the existing project docs
  (`portable-workspaces.md`, `supersession-gate.md`); the README links it
  rather than inlining it, keeping the README scannable.
- **Newcomer-first ordering:** what-it-is prose (three sentences max) sits
  between the banner and install, so the first screen answers "what is
  this" before any mechanics; engine internals (spec layout, lifecycle,
  statusline, telemetry) keep their existing content but move after the
  skills table, satisfying the unchanged `readme-documents-spec-engine`
  requirement.
- **Build order:** this member builds after `public-install` and
  `ci-lint-action` merge (epic Design: docs land last); the build flow's
  supersession gate (`git merge origin/main` + `check-base`) reconciles the
  README before any task runs, so sibling README edits are inputs, not
  conflicts.
- Risk: quickstart commands drifting from what siblings actually shipped;
  guard: building last, the quickstart's commands are copied from the
  merged README sections, not predicted.
