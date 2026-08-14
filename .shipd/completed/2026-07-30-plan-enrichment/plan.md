# plan-enrichment
Status: verified
Epic: autonomous-delivery

## Idea

Give gate-rejected plans a guided recovery: a `locate` engine verb finds the
parked change across worktrees, and `/s:plan` gains an enrichment mode that
diagnoses the in-plan findings, interviews only the true gaps, and re-gates.

### Motivation

The context-sufficiency gate parks insufficient plans at `rejected`, but
recovery is entirely manual today: nothing finds the parked worktree, and the
deliver skill points humans at a raw `set-status draft|ready` with no guided
enrichment. The epic's decision is that invoking `/s:plan` on a rejected
change — wherever its worktree lives — becomes that recovery flow.

### Details

- `spec_status.py locate <change>`: probe the invocation root's resolved
  `planned/` and each worktree directory under `.worktrees/` for the change,
  printing root, change dir, and status per match (spec-status, modified).
- `/s:plan` enrichment mode: when the argument locates a `rejected` change,
  diagnose the `## Context insufficient` findings, resolve what the codebase
  answers, interview only the true gaps, edit the installed artifacts in
  place, and re-run the gate (shipd-plan, modified).
- `/s:deliver` rejected-member pointer becomes `/s:plan <member>` instead
  of a raw status write (epic-autopilot, modified).

Impact: `plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/skills/plan/SKILL.md`, `plugins/s/skills/deliver/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json` (0.6.2 → 0.6.3). No new dependencies.

### Non-goals

- No autopilot re-drive of enriched members — re-entry stays human-initiated
  (run `/s:deliver` again, or build the member directly).
- No model or network calls in the locate verb — enrichment judgment lives in
  the skill; the engine stays deterministic.
- No new eval case for enrichment mode; the existing plan eval cases cover
  the unchanged fresh-plan flow.
- No force-promotion path: enrichment exits to `ready` only through the
  gate's verdict, never via `set-status --force`.

## Implementation

- **Locate is a filesystem probe, not git plumbing.** Worktrees are plain
  directories under `.worktrees/`, so `locate` scans the invocation root's
  resolved `planned/` first, then each `.worktrees/<name>` entry in sorted
  name order, resolving the content directory independently per candidate
  root via `spec_common.specs_dir` (a worktree can carry its own
  `.shipd-config.json`). Rejected: `git worktree list` — needs git, is awkward
  in tests, and adds nothing over the directory convention.
- **Output shape:** one keyed block per match — `change:`, `root:` (absolute
  path), `dir:` (change directory relative to that root), `status:` (`?` when
  missing or invalid) — blocks separated by a blank line, the invocation
  root's own match always first. Exit 0 on at least one match; exit 1 with an
  error naming the probed locations when none. Keyed lines match the engine's
  existing verb style and are trivially skill-parseable.
- **Enrichment edits in place and exits through the gate.** The change is
  already installed, so enrichment edits `planned/<change>/` artifacts in the
  located root directly (precedent: the gate itself rewrites `plan.md`), then
  re-runs `spec_gate.py <change>`, which lints, re-checks context, strips the
  findings section, and promotes to `ready` on pass. Rejected: re-emission
  through staging with `--replace` — it discards the installed change's
  identity and duplicates guarantees the gate already provides.
- **Mode selection is engine-mediated:** the skill runs `locate` on its
  argument before anything else. `rejected` → enrichment in the located root;
  any other located status → report location and status and stop (never a
  colliding fresh plan); no match → the normal plan flow, unchanged.
- Risk: a change parked in a worktree of a different checkout of the repo is
  invisible to `locate`; accepted — locate's not-found error names what was
  probed, so the user can move to the right checkout.
