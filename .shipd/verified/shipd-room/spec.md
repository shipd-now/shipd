# shipd-room

### Requirement: Room skill loop
id: room-skill-loop

The plugin SHALL ship `plugins/s/skills/room/SKILL.md`, invoked as
`/s:room [<pr>] [stay]`, whose workflow runs the `shipd room` verbs in this
order: `join` (with `--skill review-finding --skill question --skill status`
unless the user names skills), `list`,
then a foreground `watch <pr> --since <cursor> --timeout 540`; on a surfaced
task it SHALL post `message --task <id> --state working`, do the work, and
post the reply with an explicit `--state` (`completed`, or `input-required`
with `--to` the asker), then re-enter `watch` with the line's `cursor`. With
`stay`, an empty wait SHALL re-enter `watch` with the cursor `watch` printed
on stderr instead of ending the turn, each `watch` call still running in the
foreground with `--timeout 540`. The skill SHALL state that the tool call
running `watch` carries its own timeout above 540 seconds, so the harness
never backgrounds the wait, and SHALL name `--timeout 600` nowhere. The skill
SHALL never act on a task the `watch` output did not surface, and SHALL
resolve the agent name only through the verbs' own resolution, stopping with
the verb's `Error:` text when no name resolves.

#### Scenario: Skill names the loop's verbs in order
- **WHEN** the room skill test reads `plugins/s/skills/room/SKILL.md`
- **THEN** it finds `shipd room join`, `shipd room list`, `shipd room watch`,
  `shipd room message`, and `shipd room close` in that order of first
  appearance, and `--skill review-finding --skill question --skill status`
  and `--timeout 540`, and no `--timeout 600`

#### Scenario: Skill states the tool-call timeout
- **WHEN** the room skill test reads the skill
- **THEN** it finds the rule that the tool call's own timeout exceeds 540
  seconds, and `600000`

#### Scenario: Reply carries an explicit state
- **WHEN** the room skill test scans the skill's `shipd room message`
  invocations
- **THEN** each one carries a `--state` flag

#### Scenario: Skill documents stay mode
- **WHEN** the room skill test reads the skill
- **THEN** it finds `/s:room [<pr>] [stay]` and the rule that a `stay` turn
  re-enters `watch` after an empty wait

### Requirement: Room skill stop conditions
id: room-skill-stops

The skill SHALL end its turn and report, without posting, when `watch`
prints a `closed` line (the pull request was merged or closed), when `watch`
exits `0` with empty stdout and the skill was not invoked with `stay` (no
actionable task, reporting the cursor), when `message` exits `1` with a
round-cap `Error:` line (the verb has already posted `failed`), or when any
verb exits non-zero. On a `closed` line whose `open` array is not empty, the
report SHALL list those tasks as unresolved, with each id and state. The
skill SHALL pass the pull request URL, or `--repo` when the user names a
repository, to every verb, and SHALL run `watch` only in the foreground, and
SHALL state that a delegated worker never runs `watch` in the background.

#### Scenario: Skill states every stop
- **WHEN** the room skill test reads the skill
- **THEN** it finds the closed-room stop, the empty-watch stop scoped to a
  turn without `stay`, the round-cap stop, and the foreground-only rule for
  `watch`

#### Scenario: Skill reports unresolved tasks on a closed room
- **WHEN** the room skill test reads the skill
- **THEN** it finds the `open` array of the `closed` line and the word
  `unresolved`

#### Scenario: Skill passes the repository through
- **WHEN** the room skill test reads the skill
- **THEN** it finds `--repo` and the pull request URL named as what every
  verb receives

### Requirement: Room skill posts prose, and only the author's agent fixes findings
id: room-skill-no-code

The skill SHALL read the agent's role as the `role` on its own card in
`shipd room list <pr> --json`. While working a surfaced `review-finding`
task, an agent whose role is `author` MAY edit, commit, and push code, only
when `shipd room whoami <pr> --author` exits `0` (the acting login is the pull
request's author, a GitHub App's `app/<slug>` and `<slug>[bot]` counting as
one account), the pull request is not cross-repository (`gh pr view <pr>
--json isCrossRepository` is `false`), the working tree is on the pull
request's head branch (`gh pr view <pr> --json headRefName` equals `git
branch --show-current`), and the tree is clean: it SHALL make the smallest
change that addresses the finding, run the tests covering the touched files,
commit, push with plain `git push` and never with `--force`, and close the
task `completed` naming the commit's short SHA. If any of those checks or the
test run fails, then it SHALL push nothing and fall back to the prose
hand-off. The skill, its harness body and its reference SHALL NOT ask the
agent to compare `author.login` with `gh api user` by hand. Every other role,
and every task that is not a `review-finding`, SHALL post prose only and never
edit, commit, or push code; a task that needs a code change SHALL be answered
with a reply naming `/s:fix` or `/s:plan` as the hand-off. No agent SHALL push
to a branch other than its own pull request's head branch. A picked
`review-finding` task whose finding the PR head already addresses SHALL be
closed `completed` with a one-line note naming the commit.

#### Scenario: Skill forbids code edits
- **WHEN** the room skill test reads the skill
- **THEN** it finds the no-code rule naming `/s:fix` and `/s:plan`, and the
  text `never edits, commits, or pushes code`

#### Scenario: Skill states the author's fix rule and its guard
- **WHEN** the room skill test reads the skill
- **THEN** it finds `author`, `review-finding`, `shipd room whoami <pr>
  --author`, `isCrossRepository`, `headRefName`, `git push`, and the rule
  never to push with `--force`, and does not find `gh api user`

#### Scenario: Harness body carries the same rule
- **WHEN** `harness_bodies.render("room", ("background-tasks",),
  refs_dir="R")` runs
- **THEN** the output names `author`, `whoami <pr> --author`,
  `isCrossRepository`, `headRefName`, `/s:fix`, and `/s:plan`, and the
  reference names `whoami <pr> --author` and not `gh api user`

### Requirement: Room harness body
id: room-skill-body

The plugin SHALL ship `plugins/s/harness/bodies/room.md`, opening with a
`<!-- description: … -->` marker, and its fallback reference
`plugins/s/harness/references/room.md`. The body SHALL gate the watch loop on
`<!-- if:background-tasks -->`; its `<!-- else -->` segment SHALL run one
`shipd room list <pr> --json` read, report the actionable tasks, and end
without running `watch`. The body's watch step and the reference's watch
section SHALL name `--timeout 540`, never `--timeout 600`, and SHALL state
that the tool call's own timeout must exceed 540 seconds. `docs/room-run.md`
SHALL name `--timeout 540` wherever it shows the watch wait.

#### Scenario: Bare harness reads once
- **WHEN** `harness_bodies.render("room", (), refs_dir="R")` runs
- **THEN** the output contains `shipd room list` and no `shipd room watch`

#### Scenario: Background harness watches
- **WHEN** the body renders with `background-tasks` declared
- **THEN** the output contains `shipd room watch`, `--timeout 540`, and
  `540 seconds`, and no `--timeout 600`

#### Scenario: Reference and how-to name the new timeout
- **WHEN** the room skill test reads `plugins/s/harness/references/room.md`
  and `docs/room-run.md`
- **THEN** each contains `--timeout 540` and no `--timeout 600`

### Requirement: Room docs and registration
id: room-skill-docs

The repository SHALL ship the room concept doc and the room how-to, each
passing `docs_lint.py`. `docs/multi-agent-pr.md` SHALL be a `concept` doc
titled `# Multi-agent PR`, at 100 lines or fewer, that names the PR room as
the mechanism and explains: the room as the pull request's comment thread;
the Agent Card and the Message with its task id and state; the six task
states `submitted`, `working`, `input-required`, `completed`, `failed`, and
`canceled`; one hidden marker per comment with prose below; room traffic as
issue comments, except that a review finding's messages reply on the
finding's own review thread and a `completed` reply resolves it; that an
agent acts only on an `input-required` task addressed to it, or unaddressed
and matching a skill on its card, and never on its own last message; the
round cap `room.max_rounds` with its default of 6 and the `failed` state it
posts; and the semantic review gate as the first member, posting each finding
as a task. Its state diagram SHALL label the state `input-required` with that
exact name, and the doc SHALL NOT explain Mermaid syntax or restate a
transition the diagram shows.

The concept doc SHALL follow the main-page shape. Its level-2 headings SHALL
be `## Why a room`, `## The model`, `## Who acts when`,
`## The review gate is the first member`, `## When to use it`,
`## How to run it`, and `## Reference`, in that order, with no `## See also`.
`## When to use it` SHALL say when a pull request needs a room: more than one
agent, or an agent and a person, take turns on it. `## How to run it` SHALL
name the three ways a turn runs — `/s:room` in a developer session, the
Actions wake installed by `shipd copilot add --room`, and `shipd room run` on
a developer machine — SHALL state that the wake acts only on an addressed
task, and SHALL link `room-run.md`. `## Reference` SHALL link `room-run.md`,
`room-wake-reference.md`, `room-review-claims.md`, `agent-identity.md`,
`customise.md`, and `semantic-review.md`.

The room how-to SHALL be `docs/room-run.md`, as `multi-agent-walkthrough-doc`
states it, and `docs/pr-room.md` SHALL NOT exist. The repository SHALL list
`/s:room` in `AGENTS.md`'s skill sentence and the `docs/cheatsheet.md`
command table; `README.md` is not a registration surface. The skill tests SHALL live in
`plugins/s/skills/room/tests/test_room_skill.py`.

#### Scenario: Registration surfaces name the skill
- **WHEN** the room skill test reads `AGENTS.md` and `docs/cheatsheet.md`
- **THEN** each contains `/s:room`

#### Scenario: Doc lints clean
- **WHEN** `docs_lint.py docs/room-run.md` and
  `docs_lint.py docs/multi-agent-pr.md` run
- **THEN** each exits `0`

#### Scenario: Concept doc states the model
- **WHEN** a reader opens `docs/multi-agent-pr.md`
- **THEN** line 1 is `<!-- doc-type: concept -->`, the title is
  `# Multi-agent PR`, the file is 100 lines or fewer, and its text names
  all six task states, `room.max_rounds`, `/s:room`,
  `shipd copilot add --room`, and `shipd room run`

#### Scenario: Concept doc names the finding thread
- **WHEN** a reader opens `docs/multi-agent-pr.md`
- **THEN** it says a finding's replies go on its review thread and no
  longer says room traffic uses issue comments only

#### Scenario: Concept doc follows the main-page shape
- **WHEN** the level-2 headings of `docs/multi-agent-pr.md` are listed
- **THEN** they are `## Why a room`, `## The model`, `## Who acts when`,
  `## The review gate is the first member`, `## When to use it`,
  `## How to run it`, and `## Reference`, in that order

#### Scenario: Concept doc links its neighbours
- **WHEN** the links in `docs/multi-agent-pr.md` are resolved
- **THEN** they include `room-run.md`, `room-wake-reference.md`,
  `room-review-claims.md`, `agent-identity.md`, `customise.md`, and
  `semantic-review.md`, none names `pr-room.md` or
  `multi-agent-autonomous-prs.md`, and every link resolves to a file under
  `docs/`

#### Scenario: How-to links the concept page and the wake
- **WHEN** a reader opens `docs/room-run.md`
- **THEN** its text links `multi-agent-pr.md` and `room-wake-reference.md`,
  and `docs/pr-room.md` does not exist

#### Scenario: Concept doc carries no diagram-syntax note
- **WHEN** a reader opens `docs/multi-agent-pr.md`
- **THEN** its Mermaid block declares `state "input-required" as input`, and
  the prose outside the block contains neither `input_required` nor the word
  `hyphen`

### Requirement: The reviewer merges only from a clear room
id: room-skill-merge-rule

Before it runs `gh pr merge`, with or without `--auto`, an agent whose card
role is `reviewer` SHALL run `shipd room list <pr> --open --json`. If the
`tasks` array is not empty, then the agent SHALL NOT merge: with `stay` it
SHALL keep watching, and without `stay` it SHALL report the open tasks and
end the turn. The harness body and reference SHALL carry the same rule.

#### Scenario: Skill states the merge rule
- **WHEN** the room skill test reads the skill
- **THEN** it finds `gh pr merge`, `list <pr> --open`, `reviewer`, and
  `working` and `input-required`

#### Scenario: Harness body carries the rule
- **WHEN** `harness_bodies.render("room", ("background-tasks",),
  refs_dir="R")` runs
- **THEN** the output names `--open` and `gh pr merge`

### Requirement: A reviewer answers a review request with the shipd review
id: room-skill-reviewer-review

When an agent whose card role is `reviewer` works a surfaced task that is addressed to it and asks it to review or re-review the pull request, the `/s:room` skill SHALL have it, after claiming the task `working`, run `shipd room whoami <pr>`. On a non-zero exit it SHALL relay the `Error:` line and stop without posting a review. On a zero exit it SHALL run `/s:review <pr-url> status=auto room-agent=<to> room-to=<last_agent>`, where `<to>` and `<last_agent>` are the surfaced task's own `to` and `last_agent` fields. That review posts through `review_gate.py post --status auto` as:

- the shared branded summary comment;
- anchored inline comments, each opening a `review-finding` task addressed to the asker;
- an `APPROVE` or `REQUEST_CHANGES` review by the acting login whose body carries the full branded summary.

The skill SHALL state the status rule: where `.github/workflows/copilot-review-gate.yml` exists on the pull request's base commit, the CI gate owns `semantic-review` and the reviewer sets no status; where that file is absent (the contents read returns 404), the reviewer's post sets `semantic-review` itself; on any other read failure it sets none. The skill SHALL then close the request task `completed` with a reply naming the verdict and the summary comment URL. The reviewer SHALL NOT submit a separate freeform `gh pr review`. A re-review request after the head moved SHALL run the same command, so the one summary comment is edited in place with the earlier verdict in its Earlier-reviews block, and a new full review lands on the new head. Posting that review is not a code change: the no-code rule for non-author roles still holds. The harness body `plugins/s/harness/bodies/room.md`, its reference `plugins/s/harness/references/room.md`, and `docs/room-run.md` SHALL carry the same rule.

#### Scenario: Skill names the review command and its options
- **WHEN** the room skill test reads `plugins/s/skills/room/SKILL.md`
- **THEN** it finds `/s:review`, `status=auto`, `room-agent=`, `room-to=`, `last_agent`, and `shipd room whoami` named before the `/s:review` line

#### Scenario: Skill states both status cases
- **WHEN** the room skill test reads the skill
- **THEN** it finds `.github/workflows/copilot-review-gate.yml`, `semantic-review`, the case where the file is present (no status set), and the case where it is absent (the post sets it)

#### Scenario: Skill forbids a freeform review
- **WHEN** the room skill test reads the skill
- **THEN** it finds `gh pr review` named as one the reviewer never submits

#### Scenario: Harness body and reference carry the rule
- **WHEN** `harness_bodies.render("room", ("background-tasks",), refs_dir="R")` runs and the reference is read
- **THEN** each names `/s:review`, `status=auto`, `room-to=`, and `copilot-review-gate.yml`

#### Scenario: The how-to names the branded review and both status cases
- **WHEN** the room skill test reads `docs/room-run.md`
- **THEN** it finds `/s:review`, `semantic-review`, and `copilot-review-gate.yml` in the reviewer section

### Requirement: A walkthrough for multi-agent autonomous pull requests
id: multi-agent-walkthrough-doc

`docs/room-run.md` SHALL be the one how-to for running agents in a pull
request's room, and the main page for `/s:room` and the `shipd room` verbs: a
`how-to` of at most 150 lines, titled `# Run agents in a pull request's
room`, that passes `docs_lint.py`. `docs/pr-room.md` and
`docs/multi-agent-autonomous-prs.md` SHALL NOT exist, and no file under
`docs/` outside `docs/retros/` SHALL link either.

The page SHALL follow the main-page shape: an opening that says what the room
is in one sentence linking `multi-agent-pr.md`, that `/s:room` runs one turn
in a session, and that `shipd room run` answers each task with a headless
turn and spends tokens only when a task arrives; then `## When to use it`,
`## How to run it`, and a closing `## Reference`, in that order, with no
`## See also`.

`## When to use it` SHALL name the cases: one turn in a session, staying on a
pull request for a whole review, two unattended listeners that carry a pull
request to merge, and one reviewer for a whole repository. It SHALL state in
one sentence that the Actions wake serves a CI agent with no session, linking
`room-wake-reference.md`.

`## How to run it` SHALL hold these level-3 headings in this order:

- `### Before you start` — an open pull request and a signed-in `gh`; the
  agent name read from `--agent`, then `SHIPD_ROOM_AGENT`, then the
  `room.agent` key, with a link to `customise.md`; for unattended runs, the
  review gate installed with `/s:gate`, the merge rules applied with
  `shipd gate rules apply`, and the harness sign-in probe naming
  `claude auth login`; and one sentence that a reviewer needs its own GitHub
  account, linking `agent-identity.md`.
- `### 1. Take one turn in a session` — `/s:room <pr>`, the bare form for the
  current branch, `stay`, and the ways a stay turn ends.
- `### 2. Take a turn by hand` — `join`, `list`, `watch` with `--since 0` and
  `--timeout 540`, `message` with `--state working` and then
  `--state completed`, and `close`; that the tool call's own timeout must
  exceed 540 seconds; that the next `watch` takes the last `cursor`; and that
  `watch` runs in the foreground only.
- `### 3. Start the reviewer listener` — the single pull request command with
  `GH_CONFIG_DIR=~/.config/gh-reviewer`; that the reviewer answers each
  review task with `/s:review`, and sets `semantic-review` only when
  `.github/workflows/copilot-review-gate.yml` is absent from the base branch;
  and `shipd room run --repo` with no number, its `--state` file, `Ctrl-C`,
  and its limits to the `reviewer` and `ci` roles and one run per agent.
- `### 4. Start the author listener` — the command in the pull request's
  worktree on the default `gh` login with `--request-review`; the manual
  `shipd room message <pr> --new --to <reviewer> --skill review-finding`
  step; the re-review task after a push; and the turn on the CI reviewer's
  "Fix required" review.
- `### 5. Watch the flow` — the four actors (the author agent, the room
  reviewer agent, the CI reviewer, GitHub) and the flow step by step, with
  https://github.com/mikkel-bergmann/unkannybanny/pull/40 as the example.
- `### 6. Merge from a clear room` — `shipd room list <pr> --open --json`
  before `gh pr merge`, and one sentence on one review per head and the
  `room-review/<agent>` status, linking `room-review-claims.md`.

The page SHALL state in one sentence that only an agent with role `author`
commits a finding's fix to its own pull request while every other role
answers in prose. It SHALL NOT hold the `run` flag table, the result line's
reasons, or the account refusal rule; `room-wake-reference.md` and
`agent-identity.md` own those. `## Reference` SHALL link
`room-wake-reference.md`, naming what it lists, and `multi-agent-pr.md`,
`agent-identity.md`, `room-review-claims.md`, `customise.md`,
`semantic-review.md`, and `copilot-review.md`. Every command the page shows
SHALL match the current `shipd room` options.

#### Scenario: The page lints and fits its cap
- **WHEN** `docs_lint.py docs/room-run.md` runs
- **THEN** it exits 0, and the file has at most 150 lines with the marker
  `<!-- doc-type: how-to -->` and the title `# Run agents in a pull request's
  room`

#### Scenario: The page follows the main-page shape
- **WHEN** the level-2 headings of `docs/room-run.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: The steps run in order
- **WHEN** the level-3 headings under `## How to run it` are listed
- **THEN** they are `### Before you start`,
  `### 1. Take one turn in a session`, `### 2. Take a turn by hand`,
  `### 3. Start the reviewer listener`, `### 4. Start the author listener`,
  `### 5. Watch the flow`, and `### 6. Merge from a clear room`

#### Scenario: The listener commands are real
- **WHEN** each `shipd room run` command in the page is compared with
  `shipd room run --help`
- **THEN** every flag it uses exists

#### Scenario: The pinned strings survive the merge
- **WHEN** `docs/room-run.md` is read
- **THEN** it contains `--timeout 540`, `GH_CONFIG_DIR=~/.config/gh-reviewer`,
  `--request-review`, `--skill review-finding`, `re-review`,
  `claude auth login`, `shipd room run --repo`, `--state`, `Ctrl-C`,
  `/s:review`, `semantic-review`, `copilot-review-gate.yml`, and the #40 URL

#### Scenario: Existing docs point at it
- **WHEN** `docs/multi-agent-pr.md`, `docs/agent-identity.md`,
  `docs/room-wake-reference.md`, and `docs/room-review-claims.md` are read
- **THEN** each links `room-run.md`, and a search of `docs/` outside
  `docs/retros/` finds no link to `pr-room.md` or
  `multi-agent-autonomous-prs.md`

### Requirement: Room reference
id: room-reference-doc

`docs/room-wake-reference.md` SHALL be the lookup page for the room: a
`reference` doc titled `# Room reference`, at 250 lines or fewer, that passes
`docs_lint.py`. Its opening SHALL say that it lists the `shipd room` verbs
and the Actions wake, SHALL link `room-run.md` as the how-to and
`multi-agent-pr.md` as the model, and SHALL keep its link to
`copilot-review-reference.md`.

The page SHALL follow the main-page shape: `## When to use it`,
`## How to run it`, and `## Reference`, in that order, with no `## See also`.
`## When to use it` SHALL say when to install the wake (a CI agent answers
addressed tasks with no session) and when a local `shipd room run` serves
instead (two agents that answer each other). `## How to run it` SHALL show
the four `shipd copilot` commands the page holds today, the
`gh variable set SHIPD_ROOM_AGENT` command, and the `COPILOT_GITHUB_TOKEN`
secret.

`## Reference` SHALL hold these level-3 sections:

- `### The room verbs` — a table of `join`, `list`, `whoami`, `message`,
  `close`, `watch`, and `run`, one line each; that every verb takes a pull
  request URL or `--repo`; and what `join` edits and `--role` sets.
- `### How a turn ends` — the four endings: the pull request ends, no task
  arrives, the round cap stops the task, and a verb fails.
- `### Run flags` — a table of `--max-turns`, `--budget`, `--state`,
  `--harness`, `--model`, `--turn-timeout`, `--interval`,
  `--request-review`, and `--ci-reviewer`, each with its default.
- `### The result line` — the JSON line, every `reason` value, and the exit
  codes.
- `### The CI reviewer's review` — which review starts an author turn, that
  each review is handled once, and the wait slices.
- `### What a turn may do` — `bypassPermissions`, the author's fix with its
  guards, and the `/s:fix` and `/s:plan` hand-offs for every other role.
- `### When a run stalls` — the lock refusal, the push permission refusal,
  and a blocked pull request.
- The wake's six sections the page holds today — the managed files, the
  `shipd copilot` verb rules, the report states, the configuration, how a
  wake runs, the reply marker, and the known limits — each keeping every
  fact it holds, as level-3 headings.

The bundled `room.py` row and the "Replies wake no other workflow" limit
SHALL keep naming `shipd room run`, as `shipd-cli`'s
`copilot-room-wake-self-contained` and `room-runner`'s `room-run-tests-docs`
require.

#### Scenario: The reference lints within its cap
- **WHEN** `docs_lint.py docs/room-wake-reference.md` runs
- **THEN** it exits 0, and the file has at most 250 lines with the marker
  `<!-- doc-type: reference -->` and the title `# Room reference`

#### Scenario: The reference follows the main-page shape
- **WHEN** its level-2 headings are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Every verb and flag is listed
- **WHEN** `### The room verbs` and `### Run flags` are read
- **THEN** the first names all seven verbs `shipd room --help` lists, and the
  second names all nine flags with the defaults `shipd room run --help`
  prints

#### Scenario: The result line is complete
- **WHEN** `### The result line` is read
- **THEN** it names `closed`, `turn-cap`, `budget`, `turn-failed`,
  `watch-failed`, `claim-failed`, `preflight-failed`, and `interrupted`, and
  states which reasons exit `0`

#### Scenario: The wake facts survive
- **WHEN** the page is read
- **THEN** it names all six managed files, the four report states,
  `SHIPD_ROOM_AGENT`, `COPILOT_GITHUB_TOKEN`, the `guard`, `run`, and `reply`
  jobs, the reply marker line, and the four known limits
