# retire-report-schema
Status: verified
Theme: developer-experience

## Idea

Remove the `schema` field from the build report's header line, from the logged
build entry, and from `build_report.py`'s command line.

### Motivation

The field is write-only: `build_report.py` writes it into the build log and
nothing anywhere reads it back. Its value has never varied — all 121 entries in
the build log carry `spec-driven`, the single value the build skill hardcodes —
so it discriminates nothing while reading, in the report header, as though it
did.

### Details

- Drop `(schema: <schema>)` from the report's change-set header line.
- Drop the `schema` key from the entry `--log` appends.
- Drop the `--schema` option from `build_report.py` and its usage docstring.
- Amend the two `build-reporting` requirements that mandate it, and the two
  prose copies of the report template that show it.

Affected capabilities: `build-reporting` (modified). Impact:
`plugins/s/skills/build/scripts/build_report.py`,
`plugins/s/skills/build/SKILL.md`,
`plugins/s/harness/references/build.md`, and
`plugins/s/skills/build/tests/test_build_report.py`. No new dependencies; the
engine stays stdlib-only.

### Non-goals

- No change to the 121 existing log entries, which keep the field.
- No replacement field: the build's driver is not recorded in its place, and
  nothing new is added to the header line or the log entry.
- No change to any other reporting field — the token summary, warnings block,
  per-model table, task counts, status, and commit hash are untouched.
- No change to what reads the build log: `metrics.py` and `install_tui.py` are
  not edited, because neither ever referenced the field.

## Implementation

- **The existing 121 entries are left exactly as they are.** Nothing reads the
  key, so a stale entry carrying it is inert; the log is an append-only JSONL in
  the user's home directory with no migration machinery; and rewriting a user's
  build history to drop a field nobody reads would be a destructive change with
  no benefit. Consequence, stated so a later reader is not surprised: the log
  is heterogeneous from this change onward — entries before it carry `schema`,
  entries after it do not — which is exactly what an append-only log of a
  changing shape looks like.
- **`--schema` is removed outright rather than accepted and ignored.** The build
  skill is the only caller, and the skill and the script ship inside one plugin
  snapshot, so the two can never be version-skewed against each other; a
  tolerated-but-dead flag would be a flag with no caller and no meaning.
  Rejected: keeping it as a no-op for a transition — there is no window during
  which an older caller meets a newer script. Accepted residual: a session that
  refreshes its plugin snapshot mid-run could invoke the new script with the old
  skill's `--schema`, which argparse rejects; telemetry is best-effort and never
  blocks a build, so the cost is one skipped log append.
- **The report header loses the parenthetical entirely**, becoming
  `Change: <name> — <done>/<total> tasks, Status: <status>`. The surrounding
  structure — the token summary line above it, the warnings block below it — is
  unchanged, so only the one line moves.
- **Two prose copies of the template must both change.**
  `plugins/s/harness/references/build.md` is a hand-maintained fallback
  reference, not generated from `SKILL.md`, so editing the skill does not update
  it. `harness-command-bodies` pins only that the reference exists and that its
  id matches its body, never the template's inner text, so this needs no delta
  against that capability.
- **`--schema` is already optional**, verified by running
  `build_report.py … --log` without it: exit 0, and the appended entry carried
  `"schema": null`. So the flag's removal changes the shape written, not whether
  the call succeeds — and no task depends on making the call newly succeed.

Risk: the only reader that could break is one outside this repository that
consumes `builds.jsonl` and expects `schema` on every entry. The field is
documented nowhere outside the two requirements this change amends, and both
in-repo readers ignore it, so the exposure is limited to a consumer nobody has
written; the heterogeneous-log consequence above is the honest statement of it.
