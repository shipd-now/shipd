# readme-refresh
Status: verified

## Why

The README predates the homegrown spec engine: it still describes `/s:build`
as an "OpenSpec orchestrator", lists one skill where the plugin now ships
three (`plan`, `build`, `status`), and says nothing about the things a reader
actually needs to understand this repo today — the `am/spec/` library and
change lifecycle, the five-status pipeline, the guarded status CLI, the ☢️
statusline, or the build telemetry. A newcomer reading the README learns a
system that no longer exists.

## What Changes

- The Skills section catalogs all three current skills (`/s:plan`,
  `/s:build`, `/s:status`) with accurate descriptions — no OpenSpec
  references anywhere.
- New sections document the spec engine end to end: the `am/spec/` layout
  (masters / changes / archive), the full-ceremony change artifacts, the
  five-status lifecycle (draft → ready → active → complete → verified) with
  its pipeline ownership and guarded transitions, the `spec_status.py` CLI,
  the ☢️ statusline and its `.claude/settings.json` registration, parallel
  task groups (`[P<n>]`), and the build report/telemetry
  (`~/.shipd/config.json`, `builds.jsonl`).
- The Structure tree is updated to the real repo layout (am/spec, the three
  skills, integrations, scripts).
- The banner, install instructions, and add-a-command/skill guidance are
  retained per the existing requirements.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `project-readme`: the skills-catalog requirement is updated to the current
  three-skill set (and loses its OpenSpec wording); a new requirement makes
  the README document the spec engine, status pipeline, and statusline.

## Impact

- Modified: `README.md` only. The spec delta touches
  `am/spec/specs/project-readme/spec.md` at merge time. No code changes.
