# audit-closeout
Status: verified
Theme: reliability

## Idea

Close the spec-coverage audit: restore the sixteen remaining coverage-lost
scenarios, drop a stale epic reference that fails the library lint, and stop a
drive test leaking a process on every run.

### Motivation

An archive audit found 26 scenarios describing live behaviour that no spec
still specified; ten were restored in `restore-gate-scenarios` and sixteen were
deferred. The library lint also exits non-zero on `main` because a completed
epic names an initiative that has no brief, and the drive suite leaves a stub
worker running after every run.

### Details

- Restore the sixteen scenarios across eight requirements in seven
  capabilities, splitting one omnibus scenario into the four behaviours it
  covered — nineteen scenarios in total.
- Remove the `Initiative: context-enhancements` line from
  `.shipd/epics/mikk-knowledge/epic.md`, whose brief exists in no workspace.
- Stop `SessionStartReplacesDifferentTargetTest` leaving its replacement stub
  daemon running after the suite exits.

Affected capabilities: `copilot-review-skill`, `delivery-dashboard`,
`build-task-coordination`, `shipd-workspace`, `shipd-cli`, `shipd-config`,
`spec-status` (all modified). Impact: delta specs, one epic header line, and
`plugins/s/skills/drive/tests/test_drive_session.py`.

### Non-goals

- No behaviour change in any implementation. Every restored scenario describes
  code that already runs; a diff touching a script other than the drive test
  would mean this change went wrong.
- No new initiative brief. The named initiative exists nowhere in this
  workspace and inventing one would fabricate a record.
- No restoration of the weaker prose-only findings the audit listed separately
  — those describe behaviour that a spec reader still finds.

## Implementation

- **Restate every requirement, never replace it.** Each of the eight entries
  carries every scenario its master holds today plus the restored ones. The
  `modified-scenario-retention` rule shipped in `delta-scenario-retention`
  fails this change if a single existing title is dropped, so the mechanism
  that caught this class of bug also guards its repair.
  Verified premise: the eight masters carry 10, 10, 11, 11, 11, 16, 2 and 10
  scenarios respectively, read through `spec_status.py base-hash` and the
  master files themselves.

- **Split the omnibus rather than restoring it verbatim.** The dropped
  `Strict mode, marker verdicts, and the other paths are unchanged` covered
  four separable behaviours — the verdict-to-status mapping, strict mode's
  no-status-but-still-comment path, pending-first on pull-request events, and
  the review-event bridge's reviewer and head guards. Restoring it as one
  scenario would rebuild the thing that made it easy to delete. Rejected:
  verbatim restoration, which keeps four behaviours hostage to one title.

- **Delete the stale `Initiative:` line rather than author a brief.** The line
  arrived with the namespace port (`1afdd19`), the epic is `Status: complete`,
  and the workspace's `.shipd/` holds only `wiki/` — there is no initiatives
  tree at all. A brief invented now would assert a planning record that never
  existed. Rejected: creating `context-enhancements`, which would make the
  lint pass by fabricating history.

- **Fix the leak in the test, not the daemon.** The production replace path is
  what the test asserts and it works — the old daemon is stopped. What leaks is
  the *replacement* daemon the test starts last and never stops. The fix
  belongs in the test's teardown.

Risk: a restored scenario could describe behaviour slightly wrong and become a
false contract. Guarded by wording each against the implementation the audit
cited and by the validator exercising them against real code.
