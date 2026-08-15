# shipd-gated-merge
Status: verified
Epic: shipd-port
Theme: spec-engine

## Idea

Finish putting `shipd-now/shipd`'s default branch behind the same PR gate
shipd runs. The branch protection and the port stack landed by hand on
2026-08-14 before this change executed; what remains is the repository's merge
settings — the one setting that decides whether a landed PR produces a
`<slug>:` subject the delivery metrics can resolve — plus recording the
API-authoring mechanism this work used.

### Motivation

This change was planned against a remote where `main` was still the initial
commit and seven branches sat pushed and unmerged. Between planning and
execution the operator landed all eight pull requests through the GitHub UI and
put the protection on. The gate now exists and a real change has transited it,
so the epic's success criteria are substantively met — but the merge settings
were never set, and that omission is why every one of those eight PRs landed as
a `Merge pull request #N` commit instead of a `<slug>:` squash.

The consequence is concrete and permanent: on `main`, the slugs
`shipd-port-tool`, `shipd-engine-port`, `shipd-library-port`, and
`shipd-evals-port` have **zero** commits whose subject begins `<slug>:` (their
subjects read `tools/port.py:`, `plugins/s:`, `.shipd:`, `evals:`), while
`shipd-brand` has **two** and the exercise change `locate-current-fallback` has
**two**. Only `shipd-identity` landed with exactly one. `metrics.py`'s
`git_change_times` resolves a change's merge commit by a subject *starting*
with `<slug>:`, so shipd's own delivery board can resolve lead time for
`shipd-identity` alone and for none of the other five ported members. Fixing the
history would require a rewrite this change forbids; fixing the setting stops
the next PR from repeating it.

### Details

- Restrict shipd's merge settings to squash-only, with auto-merge enabled and
  head branches deleted on merge, so every future PR produces a `<slug>:`
  subject and can be armed with `--auto --squash --delete-branch`.
- Record the mechanism used for GitHub API writes against `shipd-now/shipd` as
  the answer to the workspace queue entry `q-shipd-pr-authoring`, naming the
  mechanism and the scope it required. No credential value is written anywhere.
- Verify the end state the hand-landing produced: the protection's required
  contexts, conversation resolution and admin enforcement; the whole port
  present on `main` with `ci` green; and the exercise change's transit of the
  gate.
- Record the `<slug>:` metrics gap in the spec as a known, accepted consequence
  rather than asserting a landing mechanism that did not happen.

Affected capabilities: `shipd-port` (modified). Impact: the `shipd-now/shipd`
remote's merge settings, and the workspace queue entry `q-shipd-pr-authoring`.
No shipd code changes and no shipd code changes.

### Non-goals

- **No history rewrite.** The six merge-commit landings stay as they are — no
  rebase, no force-push, no re-landing to manufacture `<slug>:` subjects.
- **No engine change in either repo.** `metrics.py` is not taught to resolve
  merge-commit subjects here; that would be its own change if the epic wants
  the six members' lead time back.
- No change to the protection's required contexts, which are already correct.
- No change to shipd's own protection, merge settings, or workflow.
- No credential value written into a tracked file of either repository or into
  any spec artifact.
- No autopilot run and no second exercise change.

## Implementation

- **The authoring mechanism is an operator-supplied token file, used per
  invocation and never persisted.** `gh` authenticates as `mikkel-bergmann`,
  whose token 404s on `shipd-now/shipd`; git reaches the repo through the
  `github-shipd` SSH alias under a separate key. The operator supplied a token
  at `~/.shipd-gh-token`, and `GH_TOKEN="$(cat ~/.shipd-gh-token)" gh api
  repos/shipd-now/shipd --jq .permissions` reports `"admin": true` — the scope
  the protection reads and the settings PATCH both need. Every shipd API call
  uses that env prefix. Rejected: `gh auth login --with-token`, which writes a
  second github.com account into the keyring and would change which identity
  shipd's own PRs are created under, since `gh auth switch` is global.

- **`strict` stays `false`, contrary to this change's original plan.** The
  planned base protection specified `required_status_checks.strict: true`, but
  shipd — the repo shipd is a port of, and whose workflow it inherits — runs
  `strict: false`. Under `strict: true` every PR must be up to date with `main`
  before merging, which serializes the concurrent PRs the autopilot ships and
  would put shipd's members into a permanent `BEHIND`-reconcile loop. Shipd
  runs the same autopilot, so it takes the same setting. The already-installed
  protection is therefore left exactly as it is.

- **Merge settings are restricted to squash-only even though shipd does not
  restrict them.** shipd allows merge and rebase merges and relies on its
  workflow always passing `--squash`; shipd has just demonstrated the failure
  mode of that arrangement — eight UI merges took the default merge-commit path
  and cost six members their lead-time resolution. Disabling
  `allow_merge_commit` and `allow_rebase_merge` makes the metric-preserving
  path the only path. Bringing shipd to match is deliberately out of scope
  (a stated non-goal), not an oversight.

- **The stack and exercise requirements assert the observed end state, not the
  landing mechanism.** The original delta asserted each member landed as
  exactly one `<slug>:` squash and that the exercise PR reached merged through
  an armed squash auto-merge. Neither happened: all eight are merge commits and
  [PR #8](https://github.com/shipd-now/shipd/pull/8) shows
  `autoMergeRequest: null`. What *is* true and worth asserting is that the port
  is on `main` with `ci` green, and that the exercise change transited the real
  gate — `semantic-review` posted `success` by shipd's own poster on head
  `3ed7d4f`, `ci` green, protection enforced for admins, nothing bypassed. The
  requirements are rewritten to that end state, with the metrics gap recorded
  explicitly so it is not silently lost.

- **Verification is read-only except for the push-refusal probe.** Confirming
  the branch refuses a direct push necessarily attempts one, so it uses a
  payload that would be harmless if it somehow landed: an empty commit on a
  scratch branch cut from `origin/main`, pushed at `main`, expected to be
  rejected, then deleted locally.

Risk: the merge-settings PATCH is the only mutation of remote configuration
here, and it narrows rather than widens what is permitted, so a mistake cannot
open the branch up. Guarded by re-reading the repository object and confirming
all five values.

Risk: this change's own artifacts assert facts about a remote that a later
hand-merge could again invalidate. Guarded by every verification task reading
live API state rather than a recorded value.
