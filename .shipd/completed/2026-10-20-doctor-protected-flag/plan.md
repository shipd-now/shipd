# doctor-protected-flag

Status: ready
Planned-at: 73156d3ce5cd7c38ac953d31cd0771c4a89ffd93
Gated-hash: 3a61fb1d25fb

## Idea

`shipd doctor` stops calling a protected default branch "not protected" when the token cannot read the branch's protection details.

### Motivation

A collaborator with push but not admin rights runs `shipd doctor` on shipd-now/shipd and gets a `warn protection` line saying `main` is not protected, though it is (classic protection requiring `ci` and `semantic-review`). GitHub answers the protection-details read with 404 for such a token, and doctor reads that 404 as "no protection", so the warning is false and points at a remedy the user must not run.

### Details

- **The 404 path.** When the protection-details read returns 404 and the effective branch rules decide nothing, the `protection` check reads the single-branch payload's `protected` boolean, as the 403 path already does. When it is `true`, the line is `ok`, says the branch is protected with its details needing admin access, and says the required status contexts were not checked.
- **Unchanged paths.** A readable protection payload, a branch payload reporting `protected: false`, a branch payload that cannot be read, and the ruleset paths all report exactly what they report today.
- **Docs and version.** `docs/copilot-review.md` gains one sentence on the non-admin line, and the plugin version moves up one patch.

Affected capability: `shipd-cli` (requirement `doctor-github-checks` modified).

### Non-goals

- No change to the `merge-rules` check: it reads the ruleset listing, which needs no admin permission, so its outcome does not depend on the protection details.
- No change to the `/s:doctor` remedy table: the new line is `ok`, so it offers no remedy.

## Implementation

- In `plugins/s/bin/shipd`, `check_protection` handles 403 and 404 in one branch: both call `_branch_protected`.
- When `_branch_protected` returns `True`, the detail is "`<branch>` is protected (details need admin access) — its required status contexts were not checked: the protection details returned HTTP <status> on <nwo>". The phrase "could not be verified" is kept out of the 404 line so it reads as a settled answer; the 403 line keeps its existing wording so current tests and the skill's parsing stay unchanged.
- When `_branch_protected` returns `False`, both statuses keep the "not protected" warning with the admin note.
- When `_branch_protected` returns `None`: a 403 keeps its "could not be verified" `ok` line; a 404 keeps the "not protected" warning, the behavior before this change.
- The 404 branch probe adds one extra read-only "gh api" call only when the classic read is 404 and the branch rules decided nothing; the stub-runner tests that drive a 404 add a canned branch response.
- Tests in `plugins/s/skills/build/tests/test_shipd_cli.py`: a 404 with `protected: true` reports `ok`, says "details need admin access", and does not say "not protected"; a 404 with `protected: false` still warns "not protected"; a 404 with an unreadable branch payload still warns "not protected"; existing 404 tests that expect the warning supply a `protected: false` branch payload or rely on the unreadable fallback.
- Rejected: reporting the 404 as unverifiable whenever the token lacks admin. The branch payload answers the question directly, so doctor can say "protected" instead of "unknown".

## Readiness attestation

- Problem: a non-admin token gets 404 from the protection-details read, and doctor reports a protected branch as not protected.
- Scope: one branch of `check_protection`, its tests, one doc sentence, the version bump.
- Affected: `plugins/s/bin/shipd`, `plugins/s/skills/build/tests/test_shipd_cli.py`, `docs/copilot-review.md`, `plugins/s/.claude-plugin/plugin.json`.
- Open decisions: none.
