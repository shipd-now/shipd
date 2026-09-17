# plugin-version-guard
Status: verified
Theme: reliability

## Idea

Bump the plugin version to `0.6.223`, and add the CI check that fails a pull
request touching `plugins/s/` without advancing it.

### Motivation

`AGENTS.md` states the rule plainly: every change touching `plugins/s/` bumps
the version in `plugins/s/.claude-plugin/plugin.json`, in the same pull
request. The cache snapshot is keyed by version, so a change that skips the
bump leaves `claude plugin update` a no-op and every session running the stale
skills.

Nothing enforces it. Twenty-four consecutive merges honored the rule by hand
and the twenty-fifth (#228) did not — it added a test under
`plugins/s/skills/build/tests/` and shipped with the version unchanged. The
miss was invisible until someone read the diff against the convention.

A rule kept only by habit is a rule that lapses silently. This change restores
the version this repository should already be on, and makes the next lapse a
red check instead of a discovery.

### Details

- The version advances `0.6.222` → `0.6.223`, which is also this change's own
  compliance: it touches `plugins/s/`.
- A new stdlib-only script compares the base and head versions of
  `plugin.json` and fails when `plugins/s/` changed without an increase.
- A CI step runs it on pull requests, where a base ref exists to compare.
- Tests cover the comparison logic directly, with no git or network involved.

### Non-goals

- No retroactive fix of #228. Its branch is squash-merged and gone; the bump
  here carries the version forward for both changes.
- No version scheme change. The guard asserts the version *increases*; it
  never prescribes which component moves.
- No enforcement on `push` to `main`. A squash merge has no base ref to
  compare against, and the pull request already gated it.

## Implementation

**The comparison is a pure function, the git plumbing is the caller's.** Put
the logic in `plugins/s/skills/build/scripts/version_guard.py`: a function
taking the base version string, the head version string, and the list of
changed paths, returning the finding or `None`. Parse a version by splitting
on `.` and comparing component-wise as integers, falling back to string
comparison for any non-numeric component — never `float()`, which collapses
`0.6.9` and `0.6.90`. Keep it stdlib-only per the constitution.

**What counts as touching the plugin.** A changed path counts when it starts
with `plugins/s/`. That deliberately includes test files: #228 was a test-only
change, and it is the case the guard exists to catch. It excludes
`plugin.json` itself from *triggering* the requirement — a lone version bump
is not a change that needs a bump — while still reading it for the comparison.

**The script's CLI.** `version_guard.py --base <ref> --head <ref>` resolves
both versions with `git show <ref>:plugins/s/.claude-plugin/plugin.json` and
the changed paths with `git diff --name-only <base>...<head>`, then prints the
finding and exits 1, or exits 0. Exit 2 on an unreadable manifest, naming the
ref — never a silent pass.

**The CI step.** Add a step to `.github/workflows/ci.yml` named
`Guard the plugin version`, running only on pull requests
(`if: github.event_name == 'pull_request'`), invoking the script with
`--base origin/${{ github.base_ref }} --head HEAD`. The checkout step needs
`fetch-depth: 0` so the base ref resolves; add it there.

**Tests.** `plugins/s/skills/build/tests/test_version_guard.py` covers the
pure function: a plugins/s change with an unchanged version fails; with an
increased version passes; a change touching nothing under `plugins/s/` passes
regardless of the version; `0.6.9` → `0.6.10` counts as an increase; a
decrease fails; a version-only change passes.

**The bump.** Set `"version": "0.6.223"` in
`plugins/s/.claude-plugin/plugin.json`.
