# agent-identity
Status: verified
Epic: merge-rules
Planned-at: d77b207225bc087d35f8ad6aa8de52c77cab6cee
Gated-hash: 73f568bb8aa7

## Idea

Each agent acts as its own GitHub account, and the room refuses to let an agent approve a pull request its own account authored.

### Motivation

A reviewer's agent that shares the author's `gh` login is one person to GitHub, so its approval cannot count toward required approvals, and nothing today tells the user how to give it a second account. The room skill also has no check that stops an agent from trying to approve its own pull request.

### Details

- New read-only verb `shipd room whoami <pr>`: prints the acting login, the PR author, and which credential source is active (`GH_TOKEN`, `GH_CONFIG_DIR`, or the shared `gh` login), never a token value. It exits 1 with a one-line `Error:` when the login equals the author (case-insensitive) or cannot be read.
- `/s:room` (SKILL.md, harness body and reference) runs `whoami` before any approving or change-requesting review and stops on its error.
- `room join` with role `reviewer` or `ci` warns on stderr when the login equals the author, and still joins.
- New how-to `docs/agent-identity.md`: set up the second account with `GH_TOKEN` or `GH_CONFIG_DIR`, start each agent's session with its own, verify with `whoami`; linked from `pr-room.md`, `multi-agent-pr.md`, `semantic-review.md`.

Affected capabilities: `room-acting-account` (new). Impact: `room.py`, room tests, `SKILL.md`, `harness/bodies/room.md`, `harness/references/room.md`, three docs, `plugin.json`.

### Non-goals

- No shipd config key, flag, or file that holds a token or selects an account.
- No change to `review_gate.py`: its author detection and `COMMENT` fallback belong to `gate-approves`, and a reviewer session reaches it through the same environment.
- No creation of accounts or tokens, no `gh auth switch`, no doctor checks.

## Implementation

- Account selection is the environment alone: the `gh` subprocess in `room._default_gh` already inherits `GH_TOKEN` and `GH_CONFIG_DIR`, so no code selects an account. A test pins that `_default_gh` passes no `env=`. Rejected: a config member or `--as` flag, which would add a second source and tempt tracked files to carry account state.
- `whoami` lives in `room.py` as `cmd_whoami`, reusing `_login` and a new `_pr_author(gh, ref, repo)` over `gh pr view <ref> --json author`. It mirrors the rule `gate-approves` sets in `review_gate._review_event` (equal case-insensitively, or either side unreadable, means no approval) without importing it, because the room runtime is bundled by itself under `.github/shipd-room/`. Rejected: importing `review_gate`, which that bundle lacks.
- Output is one JSON object `{"login", "author", "source", "may_approve"}` on stdout; the `Error:` path prints no JSON.
- `join` warns rather than refuses: a card is not an approval, and an unreadable login must not block joining.
- Risk: a user with one account sees `whoami` fail for a reviewer; that is the point, and the doc says to add the second account.

## Questions and answers

### Q1: How does an agent select its own account?
- **Question:** Options: (1) environment only, since `gh` inherits `GH_TOKEN` or `GH_CONFIG_DIR` and shipd adds no key; (2) a `room.gh_config_dir` config member; (3) an `--as <account>` flag. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) environment only. The epic selects identity per session by `GH_TOKEN` or a `gh` config directory, and a second source would risk account state in tracked files.
- **Queued:** q-agent-identity-account-selection
- **Relied on by:** team-merge-test

### Q2: Where does the room refuse self-approval?
- **Question:** Options: (1) a new `shipd room whoami` verb that exits 1 on author or unreadable login, required by SKILL.md before any approving review, with `join` only warning; (2) `join` refuses a reviewer or ci card; (3) both. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) the `whoami` verb plus a skill rule, with `join` warning only. A card is not an approval, and the verb gives the skill one checkable step.
- **Queued:** q-room-self-approve-refusal-site
- **Relied on by:** team-merge-test

## Readiness attestation

### Problem and motivation

A shared login makes the reviewer indistinguishable from the author, and the room has no refusal or setup guidance.

Evidence:

- Epic `merge-rules`, Decision "Identity is the account, one per role".
- `plugins/s/skills/room/scripts/room.py:478-500` reads the login only to head comments.
- `plugins/s/skills/room/SKILL.md` has no approval rule.

### Scope and non-goals

Room verb, room skill text and docs change; the review poster and config stay out.

Evidence:

- In scope: `room.py` (`_default_gh` 69-78, `cmd_join` 551-573, `build_parser` 890+).
- Out of scope: `review_gate.py`, owned by member `gate-approves`.

### Affected capabilities and files

One new capability and about ten files are affected.

Evidence:

- Capability `room-acting-account` (new); related `pr-room` requirement `room-agent-identity`, `shipd-room` requirement `room-skill-loop`.
- Files: `room.py`, `tests/test_room.py`, `tests/test_room_skill.py`, `SKILL.md`, `harness/bodies/room.md`, `harness/references/room.md`, `docs/pr-room.md`, `docs/multi-agent-pr.md`, `docs/semantic-review.md`, new `docs/agent-identity.md`, `plugin.json`.
- Runnable premise: `gh api user --jq .login` printed `mikkel-bergmann` with `GH_TOKEN` and `GH_CONFIG_DIR` unset, so the shared login is the default seam.

### No open task-shaping decision

Selection mechanism and refusal site are settled; none remain.

Evidence:

- Account selection: Q1, planner default after the oracle returned insufficient.
- Refusal site: Q2, planner default after the oracle returned insufficient.
- Unreadable login treated as refusal: follows `gate-approves` Q2.
