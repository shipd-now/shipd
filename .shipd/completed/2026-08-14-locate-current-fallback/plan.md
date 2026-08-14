# locate-current-fallback
Status: verified
Theme: developer-experience

## Idea

Make `spec_status.py locate` fall back to the currently selected change like
every sibling change-taking verb, instead of requiring an explicit argument.

### Motivation

`locate` is the only change-taking verb whose `change` argument is required;
`show`, `status`, `validate`, `set-status`, `sync`, and `check-base` all
default to the current selection via `_resolve_change`, so `locate`'s
stricter signature is an inconsistency users hit as a surprise error.

### Details

- Change the `locate` subparser's `change` argument to `nargs="?",
  default=None`, matching its siblings.
- Resolve the argument through `_resolve_change` at the top of `cmd_locate`,
  falling back to the current selection and erroring when none is set.
- Update `cmd_locate`'s docstring to state the fallback.
- Add tests covering both the fallback (a selection exists) and the error
  path (no argument, no selection).

Affected capabilities: `spec-status` (modified, `locate-verb`). Impact:
`plugins/s/skills/build/scripts/spec_status.py`,
`plugins/s/skills/build/tests/test_spec_status.py`.

### Non-goals

- No change to `locate`'s probing behavior (invocation root then
  `.worktrees/*`), output format, or exit codes once a change name is
  resolved — only how the argument is resolved.

## Implementation

- Mirror the existing `_resolve_change` pattern used by `show`, `status`,
  `validate`, `set-status`, `sync`, and `check-base` exactly, rather than
  inventing a new fallback mechanism: `p_locate.add_argument("change",
  nargs="?", default=None)` on the parser, and `change =
  _resolve_change(root, change)` as the first statement of `cmd_locate`.
  Rejected: a bespoke fallback inside `cmd_locate` — it would duplicate
  behavior `_resolve_change` already provides consistently.
- Keep the existing `StatusError` text for the not-found case unchanged; only
  the argument's source (explicit vs. selected) changes.

Risk: none beyond the usual `_resolve_change` error surface (already
exercised by the other verbs' tests); the no-argument-no-selection path is
covered by a new test.
