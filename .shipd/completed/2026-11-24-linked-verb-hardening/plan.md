# linked-verb-hardening
Status: verified
Planned-at: 50b34e57e06ae201f050f73fe676eb41b888ed5b
Gated-hash: f6fe716a5e4c

## Idea

Close the review findings on the `linked` verb, so its listing is complete and
reads the right repository.

### Motivation

A reviewer checking a consumer in a busy repository, or reviewing by URL from
another checkout, cannot trust the verb's listing: it stops at 30 open pull
requests in silence and reads the checkout's repository. Either gap can hide
an open migration and reproduce the false block the verb exists to prevent.

### Details

- Take the reviewed pull request's repository from its resolved URL.
- Request up to 200 open pull requests in the search source, and warn on
  stderr when the listing fills.
- Match `<owner>/<repo>#<number>` shorthand in the body source.
- Correct three descriptions of the search source, and add `--search <symbol>`
  to the posting reference's call.
- Tell the reviewer how to treat the full-listing warning.
- Add a test for every scenario, update the docs, and bump the version.

Affected capability: `semantic-review` (one requirement modified, one added).
Impact: `plugins/s/skills/review/scripts/review_gate.py`,
`plugins/s/skills/review/tests/test_review_gate.py`,
`plugins/s/skills/review/references/posting.md`,
`plugins/s/skills/review/references/call-site-tracing.md`,
`docs/semantic-review-reference.md`, `plugins/s/.claude-plugin/plugin.json`.
No new dependency.

### Non-goals

- No change to the harness review body or its 150-line ceiling.
- No cap on head reads; the docs name `--repo` as the bound.
- No change to the review rule's outcomes or to the severity rubric.
- No `--limit` flag on the verb; the limit is a constant.
- No change to the older verbs that also read the checkout's repository.

## Implementation

- **Repository from the URL.** `_resolve_pr` already returns the pull
  request's URL. `linked` parses `<owner>/<repo>` from it with the existing
  `_PR_URL_RE` and drops its `_resolve_repo` call. If the URL does not parse,
  `linked` calls `_fail` naming the URL. Rejected: keeping `_resolve_repo` as a
  fallback, which would restore the wrong-repository read.
- **Limit.** A module constant `LINKED_SEARCH_LIMIT = 200` feeds
  `--limit` on the `gh pr list` call. When the decoded listing holds that many
  items, `linked` writes one line to stderr:
  `review_gate: warning: the search listing reached the limit of 200 open
  pull requests in <repo>; narrow it with --search`. Stdout and the exit code
  stay as they are. Rejected: changing the output to an object with a
  `truncated` field, which would break the array contract the docs state.
- **Warning channel.** `linked` takes no stream argument; it writes through
  `sys.stderr.write`, the pattern `main` already uses for errors.
- **Shorthand.** A second module regex,
  `(?<![\w./-])([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)#(\d+)\b`, runs over the
  body after the URL regex. The lookbehind keeps it from matching inside a
  URL or a file path. A shorthand entry is read exactly like a URL entry, so
  an issue number keeps its entry with an `error` field.
- **Search with no terms stays.** `--repo` alone still lists every open pull
  request. The docstring at the top of the module, the `linked` docstring, the
  subparser help, and the reference page's source table say so.
- **Reviewer guidance.** The "List the linked pull requests first" bullet in
  `call-site-tracing.md` gains one sentence: where the verb warns that the
  listing is full, narrow `--search`, and where that is not possible, record a
  could-not-verify entry.
- **The harness body is left alone.** Its ceiling is a verified requirement
  (`harness-command-bodies`, `body-content`), settled as Q1.

Risk: the shorthand regex can match prose such as `and/or#1`. The cost is one
failed read and an entry with an `error` field, which the reviewer already
treats as could-not-verify.

## Questions and answers

### Q1: Raise the harness review body's line ceiling?
- **Question:** Should this change raise the harness review body's 150-line
  ceiling so the body can carry the full external-consumer rule? Options:
  (1) keep the ceiling and the two-line rule; (2) raise the ceiling and
  restore the full rule. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Keep the ceiling. The body is a distilled router that does not
  reproduce its skill, and it stays under 150 lines, so the two-line rule is
  the intended shape.
- **Cited:** verified/harness-command-bodies (body-content)

## Readiness attestation

### Problem and motivation

The `linked` verb can miss a migration or read the wrong repository's
timeline, which reproduces the false block it was built to prevent.

Evidence:

- `plugins/s/skills/review/scripts/review_gate.py:1810-1811` resolves the
  number from `<pr>` and the repository from `_resolve_repo`.
- `plugins/s/skills/review/scripts/review_gate.py:1861-1865` builds the
  `gh pr list` call with no `--limit`.
- The review of pull request 448 reported both as findings.

### Scope and non-goals

The change hardens one verb, corrects its descriptions, and adds tests, docs,
and a version bump. The harness body, its ceiling, and the review rule's
outcomes stay as they are.

Evidence:

- In scope: capability `semantic-review`, requirement `linked-prs-verb`.
- Out of scope: capability `harness-command-bodies`, requirement
  `body-content`, which fixes the 150-line ceiling at
  `.shipd/verified/harness-command-bodies/spec.md:93`.

### Affected capabilities and files

One capability and six files are affected.

Evidence:

- Capability `semantic-review`: `linked-prs-verb` modified (base
  782d753461e0, from `spec_status.py base-hash`); `linked-hardening-ships`
  added.
- Files: `plugins/s/skills/review/scripts/review_gate.py:1760-1876`,
  `plugins/s/skills/review/tests/test_review_gate.py:3520`,
  `plugins/s/skills/review/references/posting.md:94`,
  `plugins/s/skills/review/references/call-site-tracing.md:20`,
  `docs/semantic-review-reference.md:186-229`,
  `plugins/s/.claude-plugin/plugin.json:4`.
- Runnable premise: `gh pr list --help` printed
  `-L, --limit int  Maximum number of items to fetch (default 30)`.
- Runnable premise: `gh pr view https://github.com/cli/cli/pull/1 --json
  number,url`, run from this checkout, exited 0 and returned that URL.

### No open task-shaping decision

One decision reached the oracle, which settled it; the rest came from the
code.

Evidence:

- Raising the harness ceiling (no): settled by the oracle, Q1.
- Limit value, warning channel, shorthand form, and keeping the unfiltered
  listing: settled by investigation.
