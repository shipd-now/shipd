# getting-started-docs
Status: ready

## Idea

Add `docs/getting-started.md`, a first-real-session guide that sets up the
☕ statusline and then walks one change through `/s:plan` → `/s:build`,
explaining every artifact and every durable outcome.

### Motivation

The docs take a newcomer from install to a built change (`docs/quickstart.md`)
but never explain what the emitted artifacts are for or why the statusline is
worth registering. The user asked for a getting-started guide covering
statusline setup plus a plan/build walkthrough of the artifacts.

### Details

- New `docs/getting-started.md` with, in order: statusline registration (a
  snapshot-resolving command for install mode, the repo path for dev mode) and
  what each rendered segment means; a `/s:plan` walkthrough explaining
  `plan.md`, the per-capability delta `spec.md`, and `tasks.md` with
  grammar-accurate excerpts; a `/s:build` walkthrough naming the three durable
  outcomes (the `change/<name>` branch, the `verified/` merge, the
  `completed/` archive); and a where-to-go-next section linking
  `quickstart.md`, `what-is-shipd.md`, `.shipd/README.md`, and the README's
  skills table.

Affected capabilities: `project-readme` (modified — one ADDED requirement).
Impact: `docs/getting-started.md` (new). Docs only — nothing under
`plugins/s/` changes, so no plugin version bump.

### Non-goals

- No links added *to* the new guide from `README.md` or `docs/quickstart.md` —
  discoverability linking is a follow-up candidate; this change ships the
  guide itself.
- No restating of the requirement/delta grammar — `.shipd/README.md` stays the
  grammar authority; the guide links it.
- No settings reference beyond the statusline — plugin auto-update and
  `.shipd-config.json` stay covered by the quickstart and the README.

## Implementation

- **Install-mode registration resolves the newest snapshot at render time** —
  `bash "$(ls -d "$HOME"/.claude/plugins/cache/shipd/s/*/ | sort -V | tail -n 1)integrations/statusline.sh"`
  — because the cached script path is version-keyed and a pinned path breaks
  on every `claude plugin update`. Verified by running the command verbatim
  against the populated cache: it resolved the newest snapshot and printed
  `☕ no active specs` (exit 0). Rejected: pinning a versioned cache path
  (breaks on update) and the repo-relative path (dev-mode checkouts only).
- **The requirement lands in `project-readme`**, beside the existing
  `quickstart-doc` requirement that already governs newcomer documentation
  under `docs/` — a new capability for one document would fragment the docs
  surface.
- **Artifact examples mirror the real grammar** — modeled on
  `.shipd/README.md` and the completed `2026-08-16-quickstart-docs` change, so
  the excerpts (an ADDED requirement block, a WHEN/THEN scenario, a
  `[req:]`-tagged task) match what the engine actually emits, not invented
  shapes.
- Risk: the guide drifting as commands and paths evolve; guard: the delta's
  scenarios pin only stable surfaces (section ordering, the artifact set, the
  snapshot-resolving command's behavior) rather than transient wording.
