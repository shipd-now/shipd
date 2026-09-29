# container-spike

### Requirement: Launcher preflight and dry run
id: spike-preflight

`tools/container/spike.py` SHALL check, in order: `container` on PATH,
`container system status` exiting 0, `GH_TOKEN` set, one of
`CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` set, a non-empty git
`user.name` and `user.email`, a workspace root holding `.shipd-config.json`
that is a git toplevel, and a repo that is a git toplevel with an `origin`
remote beneath that root. If a check fails, then the launcher SHALL print
`Error: <what> — <remedy>` and exit 2 without invoking `container build` or
`container run`. Where `--dry-run` is passed, the launcher SHALL run preflight,
print the image tag, whether a build is needed, and the full `container run`
argv, and exit 0 without building or running.

#### Scenario: Missing container tool names the installer
- **GIVEN** no `container` executable on PATH
- **WHEN** the launcher runs
- **THEN** it exits 2 with an `Error:` line naming
  `https://github.com/apple/container/releases` and `container system start`

#### Scenario: Missing Claude token names setup-token
- **GIVEN** `GH_TOKEN` set and neither `CLAUDE_CODE_OAUTH_TOKEN` nor
  `ANTHROPIC_API_KEY` set
- **WHEN** the launcher runs
- **THEN** it exits 2 with an `Error:` line naming `claude setup-token`

#### Scenario: Dry run prints the plan and invokes nothing
- **GIVEN** a stub `container` on PATH that logs its argv and every check
  passing
- **WHEN** the launcher runs with `--dry-run`
- **THEN** it prints the tag and the `container run` argv, exits 0, and the
  stub log holds no `build` or `run` invocation

### Requirement: Image built by Dockerfile hash
id: spike-image

The launcher SHALL derive the image tag as `shipd-runner:` plus the first 12
hex characters of the SHA-256 of `tools/container/Dockerfile`, and SHALL run
`container build -t <tag> -f tools/container/Dockerfile tools/container` only
when `container image list --quiet` does not list the tag. The Dockerfile
SHALL start `FROM node:22-bookworm`, install Claude Code with
`npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}` from an
`ARG CLAUDE_CODE_VERSION=2.1.284`, install `gh` from the GitHub apt repository
for `arm64`, install difftastic from
`difft-0.71.0-aarch64-unknown-linux-gnu.tar.gz`, install `ripgrep` and `jq`,
and set `ENV IS_SANDBOX=1`.

#### Scenario: Present tag skips the build
- **GIVEN** a stub `container` whose `image list --quiet` prints the derived tag
- **WHEN** the launcher runs
- **THEN** the stub log holds no `build` invocation

#### Scenario: Absent tag builds once
- **GIVEN** a stub `container` whose `image list --quiet` prints nothing
- **WHEN** the launcher runs
- **THEN** the stub log holds one `build -t <tag> -f tools/container/Dockerfile
  tools/container` invocation before the `run` invocation

#### Scenario: Dockerfile edit changes the tag
- **WHEN** one byte of the Dockerfile changes
- **THEN** the derived tag differs from the previous tag

### Requirement: Launcher run invocation and result
id: spike-run

The launcher SHALL create the run directory
`~/.shipd/container/runs/<UTC yyyymmddTHHMMSSZ>/` (or `--run-dir`) and invoke
`container run --rm --name shipd-spike-<stamp> --cpus <n> --memory <size>`
with `--mount type=bind,source=<workspace>,target=/mnt/workspace,readonly`,
`--mount type=bind,source=<repo>,target=/mnt/repo,readonly`,
`--mount type=bind,source=<main checkout>,target=/mnt/main,readonly`,
`--mount type=bind,source=<run-dir>,target=/out`, `-e NAME` for each set token
variable, `-e GIT_AUTHOR_NAME=…`, `-e GIT_AUTHOR_EMAIL=…`,
`-e GIT_COMMITTER_NAME=…`, `-e GIT_COMMITTER_EMAIL=…`, `-w /workspace`, the
image tag, then `python3 /mnt/repo/tools/container/entry.py --workspace
/mnt/workspace --repo /mnt/repo --repo-path <relative path> --clone-from
/mnt/main --ref <branch or sha> --out /out --feedback <text>`. The
`<relative path>` SHALL be the repo's main checkout (the parent of `git
rev-parse --git-common-dir`) relative to the workspace root, so a linked
worktree is cloned under the registered member path while its own branch is
what gets cloned. That main checkout SHALL also be mounted at `/mnt/main` and
named by `--clone-from`, because a linked worktree's `.git` is a file whose
`gitdir:` names a host path and so cannot be cloned inside the VM; `<branch or
sha>` SHALL be `git rev-parse --abbrev-ref HEAD` in the repo, or its `git
rev-parse HEAD` sha when that prints `HEAD` for a detached checkout. For a
plain checkout the main checkout is the repo itself and the mount is still
passed. When the container exits, the launcher SHALL read
`<run-dir>/result.json`; if it carries a non-empty `pr_url`, then the launcher
SHALL print that URL on its last line and exit 0, otherwise print
`failure` and exit 1.

#### Scenario: Run argv carries the mounts and passthrough
- **GIVEN** a stub `container`, `GH_TOKEN` and `CLAUDE_CODE_OAUTH_TOKEN` set,
  and a workspace with the repo at `shipd/shipd` beneath it
- **WHEN** the launcher runs
- **THEN** the logged `run` argv holds the four mounts, `-e GH_TOKEN`,
  `-e CLAUDE_CODE_OAUTH_TOKEN`, no `-e ANTHROPIC_API_KEY`,
  `--repo-path shipd/shipd`, `--clone-from /mnt/main`, and `--ref <branch>`

#### Scenario: Worktree repo resolves to the member path
- **GIVEN** `--repo` naming a linked worktree `.worktrees/x` of the checkout
  at `shipd/shipd` beneath the workspace root
- **WHEN** the launcher runs with `--dry-run`
- **THEN** the printed argv carries `--repo-path shipd/shipd`, mounts the
  worktree itself at `/mnt/repo`, mounts the checkout at `shipd/shipd` at
  `/mnt/main`, and carries `--clone-from /mnt/main` and `--ref change/x`

#### Scenario: Result with a PR URL exits 0
- **GIVEN** a stub `container run` that writes `result.json` with `pr_url`
- **WHEN** the launcher runs
- **THEN** it prints that URL last and exits 0

#### Scenario: Result without a PR URL exits 1
- **GIVEN** a stub `container run` that writes `result.json` with an empty
  `pr_url` and a `failure`
- **WHEN** the launcher runs
- **THEN** it prints the failure and exits 1

### Requirement: Entry script clone layout and draft mode
id: entry-clone-layout

`tools/container/entry.py` SHALL `git clone <workspace mount>
/workspace/ws`, set its `origin` to the mount's `origin` URL, `git clone
<clone-from> /workspace/ws/<repo-path>` — where `--clone-from` defaults to the
repo mount — run `git checkout --quiet <ref>` in that clone when `--ref` names
a branch its `origin` carries or a sha, set that clone's `origin` to the
`origin` URL read from `--clone-from`, load `/workspace/ws/.shipd-config.json`,
set `pr-mode` to `draft`, write it back as 2-space indented JSON, and run
`gh auth setup-git`. The clone root MUST be configurable through `--root`
(default `/workspace`) so tests run it against temporary directories.

#### Scenario: Nested clones with rewritten origins
- **GIVEN** two temporary git repos, a workspace tracking
  `.shipd-config.json` and a repo, each with an `origin` URL
- **WHEN** the entry script clones them with `--repo-path shipd/shipd`
- **THEN** `<root>/ws/shipd/shipd` is a git checkout whose `origin` is the
  repo's URL and `<root>/ws`'s `origin` is the workspace's URL

#### Scenario: Worktree branch is cloned from the main checkout
- **GIVEN** a repo carrying a branch `change/x` and a linked worktree on it
- **WHEN** the entry script clones with `clone_from` naming the main checkout
  and `ref` naming `change/x`
- **THEN** the nested clone's `HEAD` is `change/x` and its `origin` is the
  repo's URL

#### Scenario: Draft mode is injected into the cloned layer
- **WHEN** the clones exist
- **THEN** `<root>/ws/.shipd-config.json` parses with `"pr-mode": "draft"`
  and every other key preserved

### Requirement: Entry script drives plan then build
id: entry-drive

The entry script SHALL drive two conversations with `session_driver.drive`
(imported with `spec_common`, `spec_status`, `spec_lint`, and `autopilot`
from the clone's `plugins/s/skills/build/scripts`), reply
`autopilot.GOAHEAD_REPLY`, four resumes, 1800 s per turn, extra args
`--plugin-dir <clone>/plugins/s --permission-mode bypassPermissions`. Plan
drive: cwd the clone root, prompt `Run /s:plan <feedback>. Investigate, spec
it, and promote it to Status: ready.` plus the reply text, graded by a
`.worktrees/<name>` whose change reads `ready` and lints clean. Build drive:
cwd that worktree, prompt `Run /s:build for the change <name>: implement
every task, then merge and archive it and open its draft PR (draft mode — do
not enable auto-merge).` plus the reply text, graded by an archived
`completed/*-<name>` and `gh pr view change/<name> --json url -q .url`
printing a URL. Each turn's stdout SHALL be written to
`<out>/<stage>-turn<N>.json`; `<out>/result.json` SHALL hold `change`,
`pr_url`, `plan_session_id`, `build_session_id`, and `failure`. The turn
runner MUST be injectable so tests drive it without a live session.

#### Scenario: Plan grade passes on a ready lint-clean change
- **GIVEN** a clone with `.worktrees/x/.shipd/planned/x` at `Status: ready`
  and lint clean
- **WHEN** the plan grade evaluates
- **THEN** it returns the change name `x`

#### Scenario: Build drive follows a passed plan drive
- **GIVEN** an injected runner that satisfies the plan grade on turn 1 and
  an injected `gh` result printing a URL once the archive exists
- **WHEN** the entry script drives
- **THEN** `result.json` carries `change`, both session ids, and that URL

#### Scenario: Exhausted plan drive records the failure
- **GIVEN** an injected runner that never yields a ready change
- **WHEN** the entry script drives
- **THEN** no build drive runs and `result.json` carries an empty `pr_url`
  and a `failure` naming the plan stage

### Requirement: Tests and CI coverage
id: spike-tests-ci

`tools/tests/test_container_spike.py` SHALL exercise the launcher through
subprocess with a stub `container` on PATH and the entry script through its
injectable seams, using only the standard library. The CI workflow
`.github/workflows/ci.yml` SHALL carry a step running
`python3 -m unittest discover -s tools/tests -v` after the eval harness step.

#### Scenario: Tools suite runs in CI
- **WHEN** the CI workflow runs
- **THEN** a step runs `python3 -m unittest discover -s tools/tests -v` and
  its failure fails the job
