## MODIFIED Requirements

### Requirement: Run tests, banner, docs, and version
id: room-run-tests-docs
base: 143d91020f9d

The run SHALL be covered in `plugins/s/skills/room/tests/test_room_run.py`
through `room.main(argv, gh=FakeGh(...), sleep=..., clock=..., runner=...)`
with no network and no real session. The `shipd` banner's `room` line SHALL
name `run`. `docs/room-run.md` SHALL be a lint-clean how-to showing the
two-terminal setup — the author in the PR worktree on the default login, the
reviewer with `GH_CONFIG_DIR=~/.config/gh-reviewer` — and SHALL be linked from
`docs/multi-agent-pr.md`; `docs/room-wake-reference.md`'s "Replies wake no
other workflow" limit SHALL point at `shipd room run`. `plugin.json` SHALL
carry a version one patch above `main`'s.

#### Scenario: Room suite passes offline
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/room/tests` runs
- **THEN** it reports `OK`

#### Scenario: The how-to lints clean and is linked
- **WHEN** `docs_lint.py docs/room-run.md` runs
- **THEN** it exits `0`, `docs/multi-agent-pr.md` links `room-run.md`, and
  `docs/room-wake-reference.md` names `shipd room run`

## ADDED Requirements

### Requirement: Review claims page
id: room-review-claims-doc

`docs/room-review-claims.md` SHALL be the main page for review claims: a
`concept` doc titled `# Review claims`, at 100 lines or fewer, that passes
`docs_lint.py`.

The page SHALL follow the main-page shape. Its level-2 headings SHALL be
`## How a runner claims a head`, `## The heartbeat`, `## Takeover`,
`## The poster fence`, `## When to use it`, `## How to run it`, and
`## Reference`, in that order, with no `## See also`. The four sections
before `## When to use it` SHALL keep every fact they hold today: the claim
ref's path, the 60-second heartbeat, both takeover cases, the `done` ref, the
three poster checks, and the three `room claim lost` lines.

`## When to use it` SHALL state that every `reviewer` and `ci` run claims a
head with no setup, and SHALL name the case for requiring the status: merges
must wait for the claimed review. `## How to run it` SHALL hold
`### Require the review status` — the `room-review/<agent>` status, its
`pending` and `success` values, the `merge.required_checks` entry, and
`shipd gate rules apply` — and `### Give the reviewer push permission`, which
states the refusal of a `reviewer` or `ci` run whose account lacks it.
`## Reference` SHALL hold `### Cleanup` and `### Limits`, the second naming
plugin version `0.6.345`, and SHALL link `room-run.md`, `agent-identity.md`,
and `semantic-review-reference.md`.

#### Scenario: The page lints within its cap
- **WHEN** `docs_lint.py docs/room-review-claims.md` runs
- **THEN** it exits 0, and the file has at most 100 lines with the marker
  `<!-- doc-type: concept -->`

#### Scenario: The page follows the main-page shape
- **WHEN** its level-2 headings are listed
- **THEN** they are `## How a runner claims a head`, `## The heartbeat`,
  `## Takeover`, `## The poster fence`, `## When to use it`,
  `## How to run it`, and `## Reference`, in that order

#### Scenario: The claim facts survive
- **WHEN** the page is read
- **THEN** it contains `refs/shipd/claims/pr-<N>/<agent>/<sha>/<gen>`,
  `SHIPD_ROOM_CLAIM`, `room claim lost`, `room-review/<agent>`,
  `merge.required_checks`, and `0.6.345`

#### Scenario: The page links its neighbours
- **WHEN** the links in `## Reference` are resolved
- **THEN** they include `room-run.md`, `agent-identity.md`, and
  `semantic-review-reference.md`, and each resolves to a file under `docs/`
