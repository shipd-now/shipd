# room-run-ci-findings

Status: ready
Planned-at: 0a0ad6eea92ef799aa5643d49528a3c56b63d9f1
Gated-hash: 615ce1f4658b

## Idea

An author `shipd room run` acts on the CI reviewer's "Fix required" review of the current head, so the author fixes or answers the CI findings without a human.

### Motivation

On unkannybanny PR 26 the grounded CI reviewer posted a correct "Fix required" review, and the author runner never saw it. The runner only wakes on room tasks, and the CI gate posts an ordinary pull request review. The PR stayed blocked until a human stepped in, which defeats the unattended run.

### Details

- **Detection.** While the role is `author`, the run checks the PR's reviews between watch slices. It acts on a review whose author login equals `--ci-reviewer` (default "github-actions[bot]"), whose commit is the current head, and whose body carries the "<!-- shipd-verdict: fix-required -->" marker.
- **Turn.** For each such review not handled yet in this run, the run spends one resumed author turn with a prompt that names the review and tells the author to fix and push, or reply with the reason. The turn counts toward `--max-turns`.
- **Re-review.** A turn that moves the head opens the existing re-review tasks, and the push itself re-runs the CI reviewer.
- **Scope of verdicts.** "Ship it" reviews and "Not a verdict" comments are ignored: neither carries the fix-required marker.
- **Docs and version.** `docs/room-run.md` describes the flag and the CI turn; the plugin version moves up one patch.

Affected capability: `room-runner` (one new requirement). Impact: `room_run.py`, the `run` parser in `room.py`, `test_room_run.py`, `docs/room-run.md`, `plugin.json`.

### Non-goals

- No change to the CI gate workflow or to the room message protocol.
- No action on review comments from human reviewers; they reach the author through room tasks or a person.
- A pushback reply does not clear the CI verdict; only a new push re-runs the CI reviewer, and a person decides otherwise.

## Implementation

### Watch slices (author role with a CI reviewer)

- When the role is `author` and `--ci-reviewer` is non-empty, each `cmd_watch` call gets `timeout = min(remaining, opts.interval * 4)` instead of `remaining`.
- A slice that returns no task line and no closed line is not the end of the run: the run checks CI reviews, then watches again while budget remains. Only when the budget is spent does the reason become `budget`.
- The "watch: no actionable task" line a slice prints on stderr is dropped. The run captures stderr for the slice and re-emits every other line.
- Reviewer and `ci` runs, and author runs with an empty `--ci-reviewer`, keep today's single full-budget watch.

### CI review check

- New helper `_ci_reviews(gh, repo, number, login, head)` reads `repos/<repo>/pulls/<n>/reviews` with `gh api --paginate`. It returns the reviews whose `user.login` equals `login` case-insensitively, whose `commit_id` equals `head`, and whose `body` contains the fix-required marker, oldest first. A failed or unparseable read warns once on stderr (key "ci-reviews" in `warned`) and returns an empty list.
- The run keeps a set of handled review ids. The check runs once right after the kick-off (so a review already on the head when the run starts is handled) and after every slice that returned no task.
- For the newest unhandled matching review, the run marks every matching id handled, then spends one turn with `_ci_prompt(url, review, login, head)` in place of the room prompt. The turn reuses the session id, the head read before and after, the re-review on a moved head, the failure handling, and the turn cap exactly as a task turn does.
- The stderr progress line is "room run: turn N on CI review <id> by <login>".

### CI prompt

- Text: "The CI reviewer @<login> asked for fixes on <url> at head <sha7>: <review html_url>. Read that review and its inline comments with gh. For each finding, fix it, commit, and push to the pull request branch, or reply on the pull request with the concrete reason it is wrong. Do not approve or merge."

### Parser

- `room.py`'s `run` parser adds `--ci-reviewer LOGIN`, default "github-actions[bot]", help "CI reviewer whose fix-required review of the head starts an author turn; empty disables". A non-author run ignores it.

### Tests

- `test_room_run.py` extends the fake gh to serve the reviews endpoint, then covers: a fix-required review on the head runs one turn with the CI prompt; a ship-it review, a review of an older head, or another login runs no turn; the same review is handled once; a pushed fix opens the re-review; a reviewer run never reads reviews; an empty `--ci-reviewer` keeps the single watch.

## Readiness attestation

- Problem: CI-bot "Fix required" reviews never reach the author runner (unkannybanny PR 26).
- Scope: author-role runner only; the gate workflow and room protocol stay unchanged.
- Affected: `plugins/s/skills/room/scripts/room_run.py`, `plugins/s/skills/room/scripts/room.py`, `plugins/s/skills/room/tests/test_room_run.py`, `docs/room-run.md`, `plugins/s/.claude-plugin/plugin.json`.
- Open decisions: none; the user chose this fix and PR 26 as its live test.
