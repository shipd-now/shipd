# room-app-identity
Status: verified
Theme: reliability

## Idea

Let a room session act as a GitHub App bot: read its login through GraphQL when `gh api user` is refused, treat `app/<slug>` and `<slug>[bot]` as one account wherever a login meets an author, and give the author's fix check one engine-backed verb.

### Motivation

The shipd-factory runs `shipd room run --role author` with a GitHub App installation token to fix findings on its own bot-opened PRs, but the room cannot see that it is the author: `gh api user` answers 403 for an installation token and `gh pr view --json author` names the bot `app/shipd-factory` while REST and GraphQL name it `shipd-factory[bot]`. The skill's hand-written author check (`author.login` against `gh api user --jq .login`) fails for the same two reasons, so the author agent can never fix its own finding.

### Details

- `room._login`: fall back to `gh api graphql -f query={viewer{login}}` when `gh api user` fails or names no login; warn and return `""` only when both fail.
- One helper, `room.login_key(login)` (lowercase; `app/<slug>` becomes `<slug>[bot]`), and `room.same_account(a, b)`, used at every login-to-author comparison: `join`'s reviewer/ci warning, `whoami`, `room run`'s start check (refusal and author warning), the CI-review author match, and repo mode's skip of the acting login's own PRs.
- `shipd room whoami <pr>` gains an `is_author` JSON field and a `--author` mode that exits 0 only when the acting login is the PR author.
- `/s:room` SKILL.md "Prose, and the author's fix" step 1, the harness body `harness/bodies/room.md` and the reference `harness/references/room.md` point the author check at `shipd room whoami <pr> --author`, keeping the `isCrossRepository`, `headRefName` and clean-tree checks.
- `docs/agent-identity.md` documents `is_author`, `--author` and the App-token case.
- Plugin version bump (one patch above main).

Affected capabilities: `room-acting-account` (added + modified), `room-runner` (modified), `shipd-room` (modified). Impact: `plugins/s/skills/room/scripts/room.py`, `room_run.py`, `room_run_repo.py`, the room tests, `plugins/s/skills/room/SKILL.md`, `plugins/s/harness/bodies/room.md`, `plugins/s/harness/references/room.md`, `docs/agent-identity.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to `review_gate.py`'s self-approval check in the review skill; it reads `gh api user` on its own and already degrades to a `COMMENT` review when that fails.
- No minting or refreshing of installation tokens; the caller supplies `GH_TOKEN`.
- No change to behaviour for ordinary user tokens: `gh api user` stays the first read, and two user logins compare exactly as before (case-insensitively).

## Implementation

- **Fallback read.** `_login` keeps `["api", "user"]` as the first call. When it exits non-zero or yields an empty login, it calls `["api", "graphql", "-f", "query={viewer{login}}"]` and reads `data.viewer.login`. The memo still caches the result, so each verb reads at most once per source. The warning text when both fail stays today's (`warning: could not read the GitHub login (gh api user...)`). Rejected: GraphQL first — it would change the call sequence for every user token for no gain.
- **Normalisation helper.** In `room.py`: `login_key(login)` returns `""` for a non-string or blank value; otherwise strips, lowercases, and maps a `app/<slug>` prefix to `<slug>[bot]`. `same_account(a, b)` is true only when both keys are non-empty and equal. Every site listed in Details calls `same_account` (or compares `login_key` values, for `_ci_reviews`'s precomputed wanted key) instead of `.lower()`. `room_run.py` and `room_run_repo.py` call `room.same_account` — no second copy. Rejected: normalising at read time inside `_pr_author` — it would change the author string printed by `whoami` and the warnings; the printed values stay as GitHub returned them.
- **whoami.** Default mode is unchanged in its exit codes and errors; its JSON gains `"is_author": false`. `whoami <pr> --author` (a `store_true` flag on the `whoami` parser) is the author's check: with login and author both readable and `same_account` true, it prints `{"login", "author", "source", "is_author": true, "may_approve": false}` and exits 0; when they differ it prints one `Error:` line `acting as @<login>, but <repo>#<n> was authored by @<author>; only the author may fix its findings` and exits 1; an unreadable login or author is the same `Error:` line as the default mode's and exit 1. It writes nothing to GitHub in either mode. Rejected: making default whoami exit 0 for the author with `may_approve` false — it would silently break every reviewer flow that stops on non-zero.
- **Error text.** The unreadable-login errors in `whoami`, `room run` and repo mode say `(gh api user and the GraphQL viewer failed)` instead of `(gh api user failed)`.
- **Skill text.** Step 1 becomes: run `shipd room whoami <pr> --author`; it exits 0 with `is_author` true only when the acting login is the PR author, counting a GitHub App's `app/<slug>` and `<slug>[bot]` as one account. Then `gh pr view <pr> --json headRefName,isCrossRepository`: `isCrossRepository` false, `headRefName` equal to `git branch --show-current`; `git status --porcelain` prints nothing. The body and reference say the same. `author.login` and `gh api user --jq` disappear from all three; `test_room_skill.py`'s needles move to `whoami <pr> --author` and `is_author`.

Risk: a token that can read neither `/user` nor GraphQL `viewer` still yields `""` and the existing refusals; that is the intended floor.

## Readiness attestation

### Problem and motivation

An App installation token cannot be read as an identity by `_login`, and gh names the bot differently from REST/GraphQL, so the factory's author session never recognises its own PR.

Evidence:

- `plugins/s/skills/room/scripts/room.py:489-511` reads only `gh api user`.
- `room.py:514-527` returns `author.login` from `gh pr view --json author`; the caller's live run showed `{"is_bot":true,"login":"app/shipd-factory"}` and GraphQL `viewer` returning `shipd-factory[bot]`.
- `plugins/s/skills/room/SKILL.md:172-176` hand-compares `author.login` with `gh api user --jq .login`.

### Scope and non-goals

Room scripts, the room skill's three text surfaces, one doc and the version; the review gate and token minting stay out.

Evidence:

- Comparison sites: `room.py:629`, `room.py:702`, `room_run.py:81`, `room_run.py:85`, `room_run.py:150-158`, `room_run_repo.py:309`.
- Out of scope: `plugins/s/skills/review/scripts/review_gate.py` is not edited.

### Affected capabilities and files

Three capabilities and the files listed in Details.

Evidence:

- `room-acting-account`: `room-whoami-verb` (base dceec222f7db); `room-runner`: `room-run-start` (base 2ad4ae6cb1ab); `shipd-room`: `room-skill-no-code` (base 193e5d33be90), hashes from `spec_status.py base-hash`.
- Runnable premise: `python3 -m unittest discover -s plugins/s/skills/room/tests` → `Ran 398 tests`, `OK` on the base.
- Runnable premise: `gh api graphql -f query='{viewer{login}}'` with a user token → `{"data":{"viewer":{"login":"mikkel-bergmann"}}}`, the shape the fallback parses.

### No open task-shaping decision

Every decision is settled by the caller's brief or above; none remain.

Evidence:

- Fallback order, helper rule and the `is_author` report: given in the brief.
- `--author` flag over changing default exit codes: settled above, keeping reviewer flows unchanged.
