# room-action-wake
Status: verified
Epic: pr-room
Theme: developer-experience

## Idea

Add the managed `room-wake.yml` workflow template and its pinned room
runtime, installed through `shipd copilot add --room`, so a room task
addressed to a repository's CI agent wakes the Copilot CLI and posts its reply.

### Motivation

After `room-watch` lands, a room task only gets answered while some
developer's session is running `shipd room watch`. An agent with no session
cannot be woken on a PR, so a task addressed to it sits at `input-required`
until a person starts one.

### Details

- New `plugins/s/integrations/copilot/room-wake.yml`: three jobs, `guard` →
  `run` → `reply`.
- `plugins/s/bin/shipd` `copilot` verb: a `--room` flag that manages the
  wake set: the workflow plus five byte-identical runtime files under
  `.github/shipd-room/`. The bare report also lists the wake set.
- Tests: `plugins/s/skills/build/tests/test_copilot_verb.py` (verb) and a
  new `plugins/s/skills/room/tests/test_room_wake.py` (template).
- A new `docs/room-wake-reference.md` covers the wake set, linked from
  `docs/copilot-review-reference.md` (already at its line cap). The plugin
  version goes one patch above `main`'s value at build time.

Affected capabilities: `pr-room` (added by `room-schema`; ADDED only),
`shipd-cli` (`copilot-verb` modified, one requirement added). This change
depends on `room-schema`, `room-cli-verb` and `room-watch` merging first. It
uses their `room.py` verbs and `watch` NDJSON as given and re-specifies
none of their requirements.

### Non-goals

- No change to `room.py`, `room_schema.py`, the gate templates, or `/s:gate`.
  Plain `copilot add`/`remove` still manage exactly the four gate files.
- No action on unaddressed, skill-matched tasks. The wake answers only tasks
  whose `to` names `SHIPD_ROOM_AGENT`.
- No `doctor` check, no secret or variable setup, and no fork-PR support.
  On a fork, the token is read-only.

## Implementation

- **Runtime is bundled, not fetched (Q1).** `add --room` copies these plugin
  files byte-identical into `.github/shipd-room/`, keeping their
  plugin-relative paths:
  - `.claude-plugin/plugin.json`
  - `skills/room/scripts/room.py`
  - `skills/room/scripts/room_schema.py`
  - `skills/build/scripts/spec_common.py`
  - `skills/build/scripts/cli_common.py`

  This keeps `room.py`'s own `sys.path` insert and manifest read working
  unchanged. The guard reuses `is_actionable` by running the bundled
  `room.py watch` instead of carrying an inline copy, so there is one
  predicate with no drift, pinned to the install version the way
  `semdiff.py` is. The workflow runs the bundled `room.py` directly. That is
  the same verb `shipd room` execs, with the same output and exit code.
  Rejected: checking out `shipd-now/shipd` (no version tags exist, so the
  ref would float); an inline predicate (a second copy to drift).
- **Opt-in flag (Q2).** `shipd copilot [add|remove] --room` acts on the wake
  set only. Plain `add`/`remove` act on the four gate files only. The bare
  report lists all ten files under two headings. The wake workflow carries
  `# shipd-copilot v{version}`. A runtime file counts as owned exactly when
  that workflow does; it is `stale` when its bytes differ, and the workflow
  is `stale` while any runtime file is not `installed` (the semdiff rule).
  Foreign refusal, `--force`, atomic writes and prepare-before-write all
  follow `copilot-verb`. `remove --room` prunes the emptied
  `.github/shipd-room/` directories innermost first.
- **Three jobs (Q3).**
  - `guard`: repository token. Checks out the default branch.
  - `run`: `COPILOT_GITHUB_TOKEN` only. Checks out `refs/pull/<n>/head`
    with `persist-credentials: false`.
  - `reply`: repository token, on a fresh runner. Checks out the default
    branch and runs `if: always()` when the guard passed.

  The steered runner shares no filesystem, `$GITHUB_PATH` or `$GITHUB_ENV`
  with a credentialed step. The reply crosses jobs only as a job output,
  read through `env:` and never interpolated into a script.
- **Triggers and prefilter.** `issue_comment` and
  `pull_request_review_comment`, `types: [created]`. The guard job runs only
  when all of these hold:
  - `vars.SHIPD_ROOM_AGENT` is set;
  - the comment body contains `<!-- shipd-room `;
  - the event is a review comment or the issue is a PR.

  Concurrency: group `shipd-room-wake-<comment id>`, no cancel.
- **Guard step.** It exits not-actionable with a log line when the
  `COPILOT_GITHUB_TOKEN` secret is absent. Otherwise it runs
  `room.py watch <pr> --once --since <cursor>` (the `<issue>:<review>` pair:
  `<id - 1>:0` for an issue comment, `0:<id - 1>` for a review comment) as
  `SHIPD_ROOM_AGENT`. Empty stdout means not actionable, per room-watch's
  empty-exit rule. It keeps the line whose `comment` equals the event's
  comment id and whose `to` equals the agent; the task id is the `task` key,
  else `id`. It then `join`s with `--harness copilot-cli` only when
  `list --json` holds no card of that name, and posts
  `message <pr> --task <id> --state working -- "picked up by the CI wake"`.
  Outputs: `actionable`, `pr`, `task`, `asker` (`last_agent`), `text`.
- **Runner step.** `npm install -g @github/copilot@1.0.80`, the gate's pin.
  `timeout ${SHIPD_ROOM_CLI_TIMEOUT:-600} copilot -p "$prompt"
  --allow-all-tools`. The prompt names the agent, the PR, the asker and the
  task text, and explains the reply marker. The reply is truncated to
  60000 characters.
- **Reply state (Q4).** If the reply's last non-blank line is exactly
  `<!-- shipd-room-reply: input-required -->`, the reply step strips it and
  posts `input-required`. Otherwise it posts `completed`. Both go `--to`
  the asker via `room.py message <pr> --task <id> --state <s> -- "$text"`.
  When the run failed or the reply is empty, it posts
  `close --task <id> --state failed --reason wake-runner-failed` instead. A
  round-cap refusal from `message` exits `1` and fails the job.
- **Credential hygiene.** Every `room.py` call runs as `/usr/bin/env -i
  PATH=/usr/bin:/bin HOME="$HOME" GH_TOKEN=… GH_REPO=… SHIPD_ROOM_AGENT=…
  /usr/bin/python3 -B …`.

Risk: a reply posted with `github.token` starts no workflow, so two CI
agents in one repository never wake each other. This is documented as a
known limit. Risk: a sibling member's names drift before merge; the first
task re-reads the merged modules and stops on any missing symbol.

## Questions and answers

### Q1: Where does the wake workflow get the room runtime?
- **Question:** Options: (1) bundle it byte-identical under
  `.github/shipd-room/`, owned with the workflow, as `semdiff.py` is
  bundled; (2) check out `shipd-now/shipd` at a ref from a variable,
  default `main`; (3) an inline Python predicate and poster.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. It is pinned to the install version, and the guard
  reuses `room.py`'s predicate instead of copying it. No version tags exist,
  so option 2 would float.
- **Queued:** q-pr-room-wake-runtime-source

### Q2: How does the copilot verb family install the wake?
- **Question:** Options: (1) opt-in `copilot add|remove --room`, with the
  bare report listing the wake set; (2) plain `add` installs it
  unconditionally and `/s:gate` commits the extra paths; (3) a separate
  verb. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. It keeps the four-file contract and `/s:gate`'s
  "exactly the four managed paths" commit unchanged, and it stays in the
  same verb family the epic names.
- **Queued:** q-pr-room-wake-install-surface

### Q3: How is the runner kept apart from the repository token?
- **Question:** Options: (1) three jobs, `guard`, `run`, `reply`, with the
  reply passed as a job output; (2) one job of three steps, hardened like
  the gate. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. It is the gate's two-credential separation enforced
  by a VM boundary. Separate jobs leave nothing a runner step can write
  (workspace files, `$GITHUB_PATH`, `$GITHUB_ENV`) to reach the
  credentialed step. The epic's Design prose says "step"; if this default
  stands, an epic amendment rewords that sentence to name jobs.
- **Queued:** q-pr-room-wake-job-isolation

### Q4: What state does the wake's reply carry?
- **Question:** Options: (1) `completed` to the asker, or `input-required`
  back when the runner ends with a reply marker; (2) always `completed`;
  (3) always `input-required`. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. The epic allows both states, `completed` first. The
  marker's exact form is the planner's implementation detail.
- **Cited:** epic/pr-room

## Readiness attestation

### Problem and motivation

No agent without a live session can be woken by a room task.

Evidence:

- Epic `pr-room` Decision "Local poll first, CI wake second". Its Design
  section describes the "CI wake (`room-wake.yml` template)".

### Scope and non-goals

The change covers the template, the `--room` verb surface, the tests, the
docs and the version. The room verbs, the schema, the gate and `/s:gate`
are not changed.

Evidence:

- Epic Changes table, row `room-action-wake`.
- `plugins/s/skills/gate/SKILL.md:337` commits "exactly the four managed
  paths". That is why `--room` is opt-in.

### Affected capabilities and files

Two capabilities and five files are affected.

Evidence:

- `shipd-cli` `copilot-verb` (base c979c80aabe7, from `base-hash`). `pr-room`
  is added by `room-schema`.
- Files: `plugins/s/bin/shipd:1575-1841`, the new template,
  `test_copilot_verb.py`, the new `test_room_wake.py`, and
  `docs/copilot-review-reference.md`.
- Precedent: `copilot-review-gate.yml:245-293`, which holds the pinned CLI
  and the token binding.
- Runnable premise: `version_guard.py --base main --head HEAD` → exit 0.
  `gh repo view shipd-now/shipd --json visibility` → `PUBLIC`.
  `git ls-remote --tags origin` → only `schema-v1.0.0`.

### No open task-shaping decision

Every decision is settled.

Evidence:

- Q4 was settled by the oracle. Q1-Q3 are PLANNER defaults.
- Addressed-only acting comes from the epic's Design guard wording.
