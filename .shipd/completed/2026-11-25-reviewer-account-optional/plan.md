# reviewer-account-optional
Status: verified
Planned-at: 1935e7dad7596f87e1211c2ec4e6aaae845d2b88
Gated-hash: 0532aaa82547

## Idea

Let a room reviewer act on the pull request author's own account by default, and add a `distinct_reviewer` config key that restores today's refusal for teams that need separate accounts.

### Motivation

A solo developer cannot run a room reviewer on their own pull request, because `shipd room run`, `shipd room whoami` and the `/s:room` skill refuse the author's account and no setting changes that. The owner wants one posted shipd review to be enough by default, while an enterprise can still require a separate reviewer account.

### Details

- A new top-level config key, `distinct_reviewer` (`true` or `false`, default `false`).
- `shipd room run --role reviewer|ci` on the author's account warns and continues by default, and refuses only when the key is `true`.
- `shipd room whoami` on the author's account exits `0` with `may_approve` false by default, and refuses only when the key is `true`.
- Repo mode answers pull requests the acting account authored by default, and skips them only when the key is `true`.
- The `/s:room` skill and its two harness copies say a `may_approve` false review posts as a comment.
- Five docs pages follow, and the plugin version moves one patch.

Affected capabilities: `shipd-config` (one added requirement), `room-acting-account` (three modified), `room-runner` (two modified). Impact: `plugins/s/skills/build/scripts/spec_common.py`, `plugins/s/skills/build/scripts/config_registry.py`, `plugins/s/skills/build/references/shipd.config.example.json`, `plugins/s/skills/room/scripts/room.py`, `room_run.py` and `room_run_repo.py`, `plugins/s/skills/room/SKILL.md`, `plugins/s/harness/bodies/room.md`, `plugins/s/harness/references/room.md`, four test files, `docs/agent-identity.md`, `docs/room-run.md`, `docs/multi-agent-pr.md`, `docs/pr.md`, `docs/customise.md` and `plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to `review_gate.py`: it already posts a comment review and the status from the author's account.
- No change to the `merge` key or its default of two approvals; the docs give the single-account values.
- No change to `shipd room join`, which keeps its warning, or to `whoami --author`.
- No change to how an unreadable login or author is handled: both stay errors.
- No edit to the workspace wiki here; the build's teach step rewrites the page `agent-own-account` from the ledger below.

## Implementation

- **The key.** `distinct_reviewer` is a top-level boolean (Q1). In `spec_common.py`: add it to `RECOGNIZED_CONFIG_KEYS`, add `distinct_reviewer_from_config(config, prov)` returning the bool and raising `ConfigError` on a non-boolean, and `resolve_distinct_reviewer(root)` over `resolve_config`, modelled on `resolve_pr_mode`. In `config_registry.py`: one `_row("distinct_reviewer", _boolean("distinct_reviewer"), "true or false", "repo")`, in key order. In the config example: a `// distinct_reviewer` entry after `// room`. Rejected: a `room` member, because `room` merges wholesale and a repository setting it would hide each developer's `room.agent`; a `merge` member, because `merge` maps to a GitHub ruleset and this has no ruleset equivalent.
- **One reader in the room.** `room.py` gains `_distinct_reviewer(root)`, which calls `spec_common.resolve_distinct_reviewer` and turns `ConfigError` into `RoomError`, as `room.py` line 329 does for `resolve_room`. `cmd_whoami`, `room_run._check_identity` and repo mode all call it, with the root each already resolves.
- **`whoami`.** Same account and key `false`: emit the JSON with `is_author` true and `may_approve` false, exit `0`. Same account and key `true`: `RoomError` reading `acting as @<login>, who authored <repo>#<n>; distinct_reviewer requires a reviewer account other than the author's`. `--author` and the unreadable cases keep their code.
- **`run` start.** `_check_identity` takes the resolved flag. Reviewer or `ci` on the author's account: key `true` raises the same `RoomError`; key `false` writes `warning: acting as @<login>, who authored <repo>#<n>; the review posts as a comment, not an approval` to stderr and continues. An unreadable author stays an error.
- **Repo mode.** `room_run_repo.py` reads the flag once at start. The skip at line 309 keeps the empty-author case always, and applies the same-account case only when the flag is `true`.
- **Enforcement (Q2).** The key governs the room verbs only. A team that needs a tamper-proof rule keeps `merge.approvals` at 1 or more, which GitHub enforces.
- **Skill copies.** `SKILL.md`, `harness/bodies/room.md` and `harness/references/room.md` each say: `whoami` exits non-zero, stop; exits `0` with `may_approve` false, review anyway, and the review posts as a comment with its status. No heading changes, so `external-loaders.json` holds.
- **Docs.** Revise the five pages against `plugins/s/skills/document/references/standard.md`, and run `docs_lint.py` on each until it exits `0`. `docs/pr.md` gains the single-account values (Q3): `merge.approvals` `0` with `semantic-review` required makes the author's own posted review the gate; dropping `semantic-review` from `required_checks` removes it.
- **Version.** `plugin.json` moves to one patch above `main`'s at build time.

Risk: a team that relied on the refusal loses it silently on upgrade. The docs name the key, and required approvals on GitHub still block an unreviewed merge.

Risk: the wiki page `agent-own-account` still states the old rule until teach runs. The ledger entry Q2 carries the new position and is already answered in the queue.

## Questions and answers

### Q1: Which key requires a distinct reviewer?
- **Question:** Should the setting be a new top-level key, a member of `merge`, or a member of `room`? Recommendation: a new top-level boolean, default false.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** A new top-level key, default false.
- **Queued:** q-reviewer-distinct-account-key

### Q2: How strongly is it enforced?
- **Question:** Should only the room verbs refuse, should the review poster refuse too, or should there be no key at all? Recommendation: the room verbs refuse, with GitHub's required approvals as the backstop.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** The room verbs refuse. A separate reviewer account is optional by default, because what matters is that a shipd review is posted; GitHub's required approvals stay the hard backstop.
- **Queued:** q-reviewer-distinct-account-enforcement

### Q3: Does the default of two approvals change?
- **Question:** Should `merge.approvals` keep its default of 2, or drop to 0 now that one account may review its own pull request? Recommendation: keep 2 and document the single-account value.
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** It must be configurable per repository. It already is, from 0 to 10, so the default stays and the docs give the single-account values.
- **Queued:** q-merge-approvals-default-single-account

## Readiness attestation

### Problem and motivation

The room refuses a reviewer on the author's own account with no setting to change it; the owner wants one account to work by default and a switch for teams.

Evidence:

- `plugins/s/skills/room/scripts/room_run.py:67-88` raises on a reviewer or `ci` that shares the author's account.
- `plugins/s/skills/room/scripts/room.py:755-758` makes `whoami` exit 1 for the author.
- Capability `shipd-config`, requirement `room-config-key`: the `room` key holds only `agent` and `max_rounds`.

### Scope and non-goals

The change adds one key and makes three refusals depend on it; the poster and the merge rules stay as they are.

Evidence:

- In scope: the files under Details.
- Out of scope: `plugins/s/skills/review/scripts/review_gate.py:1252-1257` already posts comment-only for the author, and `spec_common.py:1416-1423` (`DEFAULT_MERGE`) takes no edit.

### Affected capabilities and files

Three capabilities and about nineteen files are affected, because the key needs a resolver, a registry row and a sample entry, three scripts read it, and the skill copies and docs state the rule.

Evidence:

- `shipd-config`: new requirement `distinct-reviewer-key`.
- `room-acting-account`: `room-whoami-verb` (base 765e7d0f8738), `room-skill-identity-check` (base 4b9d3b41e7a7), `agent-identity-docs-version` (base e74f59945a34), hashes from `spec_status.py base-hash`.
- `room-runner`: `room-run-start` (base d4998752aa46), `room-run-repo-poll` (base da2c5fb513dd).
- Files: `room_run_repo.py:300-314` holds the repo-mode skip; `spec_common.py:1225` holds `resolve_pr_mode`, the resolver pattern.
- Runnable premise: `spec_status.py config-set voice maybe` in a scratch repository → exit 1, `must be true or false`, hint `true or false`.
- Runnable premise: `spec_status.py config-set distinct_reviewer true` today → exit 1, `unknown key distinct_reviewer`.
- Runnable premise: `python3 -m unittest discover -s plugins/s/skills/room/tests -p test_room_run.py` → 68 tests, OK.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Key placement, enforcement strength and the approvals default: settled by the user, Q1 to Q3.
- Unreadable login or author stays an error, repo mode follows the same flag, and `join` keeps its warning: settled by investigation, as the smallest change that meets the request.
