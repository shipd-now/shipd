# drift-outside-root-paths
Status: verified

## Idea

Stop the drift verb from crashing on a cited path that resolves outside the repository root.

### Motivation

`autopilot.py <epic> --preflight` failed its drift check with `drift verb exit 1: Error: git log --format=%h 77880ce..77880ce -- ../../docs/context-measurement-method/doc.md failed: fatal: ... is outside repository`. A second run failed the same way on `../scripts`, cited in a member plan as relative to another directory. One such token kills the whole drift run, for every member of the epic.

### Details

- `spec_status.py drift` drops a cited path whose normalized form escapes the hosting root (a leading `..` segment after normalization) or is absolute, before it reaches `git log`.
- A dropped path is never a finding, so it cannot fail the run, in the same spirit as the `artefacts/` and version-bump exemptions already dropped there.
- Regression tests cover `../`-relative tokens, a token that escapes after normalization (`a/../../x`), and an absolute path outside the repository.

Affected capability: `spec-status` (requirement `drift-verb` modified). Impact: `plugins/s/skills/build/scripts/spec_status.py`, `plugins/s/skills/build/tests/test_spec_status.py`, and the plugin version.

### Non-goals

- No new `skipped` field in the drift output or JSON contract; the dropped path is silent, like the existing exemptions.
- No attempt to resolve a `../` token against the citing file's own directory.
- No change to `sc.cited_paths`, which the context gate and other callers share.

## Implementation

- **Where.** Filter inside `_drift_cited` (`plugins/s/skills/build/scripts/spec_status.py`), the single place that already drops `artefacts/` references and the version-bump exempt paths. `_drift_file_findings` then only ever sees in-repository paths, so `_git_capture` keeps raising on a real git failure (a bad stamp or base stays loud).
- **Test.** A path is outside the root when `os.path.isabs(p)` is true, or when `posixpath.normpath(p)` equals `..` or starts with `../`. Paths are compared relative to the hosting root, the root every drift git call is anchored on. The original spelling is kept for in-repository paths, so existing output does not change.
- **Absolute paths.** `sc.PATH_TOKEN_RE` already rejects a token starting with `/`, so an absolute token never reaches `_drift_cited` today; the `isabs` check is defensive, and the absolute-path regression test pins the end-to-end behavior (no crash, clean exit).
- **Rejected:** catching the git error per path in `_drift_file_findings`. It would also hide genuine failures, such as an unreadable repository, as silent non-drift.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` from `0.6.348` to `0.6.349`.

Risk: low. The filter only removes tokens that made git exit fatally.

## Readiness attestation

### Problem and motivation

A `..`-escaping cited path makes `git log` exit fatally and fails the whole drift run with exit 1.

Evidence:

- `plugins/s/skills/build/scripts/spec_status.py:1518` passes each cited path to `_git_capture(... "log", ... "--", path)`, which raises on a non-zero git exit.
- `plugins/s/skills/build/scripts/spec_common.py:3267` `PATH_TOKEN_RE` accepts `..` as a segment, so `../../docs/x/doc.md` and `../scripts` are cited paths.

### Scope and non-goals

The fix is one filter in `_drift_cited` plus regression tests; output contracts and `cited_paths` stay unchanged.

Evidence:

- In scope: `_drift_cited` at `plugins/s/skills/build/scripts/spec_status.py:1485`.
- Out of scope: `sc.cited_paths`, the drift JSON shape, and `autopilot.py`.

### Affected capabilities and files

One capability requirement and three files.

Evidence:

- `spec-status` requirement `drift-verb`, base `34a7fcc2d321` from `spec_status.py base-hash spec-status drift-verb`.
- Files: `plugins/s/skills/build/scripts/spec_status.py`, `plugins/s/skills/build/tests/test_spec_status.py` (`DriftTest`), `plugins/s/.claude-plugin/plugin.json`.

### No open task-shaping decision

Skip-silently versus report-as-skipped is settled: skip silently, which the request allows and which keeps the output contract unchanged.

Evidence:

- The request states a skipped path may be reported "at most" as a skipped reference, and that a single bad token must never fail the run.
