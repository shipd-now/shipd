# The Apple `container` spike

Hand one piece of user feedback to an agent that plans it, builds it, and stops
at an open draft pull request — all inside a local Linux VM, with the host's
checkouts mounted read-only.

Three files:

| File | Runs | Does |
| --- | --- | --- |
| `spike.py` | the host | preflight, image build, `container run` |
| `entry.py` | the VM | clone, inject draft mode, drive `/s:plan` then `/s:build` |
| `Dockerfile` | the build | the arm64 runner image (Claude Code, gh, difftastic, git, python3, ripgrep, jq) |

## Prerequisites

- **macOS 26 on Apple silicon.** Apple's `container` runs each container in its
  own lightweight VM; the image is arm64 only.
- **The `container` CLI**, from the signed package at
  <https://github.com/apple/container/releases>, with its service started:

  ```
  container system start
  ```

- **A GitHub token**, so the VM can push the branch and open the PR:

  ```
  export GH_TOKEN=$(gh auth token)
  ```

- **A Claude Code credential**, either an OAuth token or an API key:

  ```
  export CLAUDE_CODE_OAUTH_TOKEN=$(claude setup-token)
  ```

- **A git commit identity** (`git config user.name` / `user.email`), which the
  launcher passes into the VM as the four `GIT_*` variables.

The launcher checks all of this before it builds or runs anything, and reports
any failure as `Error: <what> — <remedy>`, exit 2.

## Usage

```
tools/container/spike.py [--dry-run] "<the user feedback>"
```

The worked example — the feedback this spike was built to drive:

```
tools/container/spike.py "I want to learn more in the onboarding skill about \
how to configure workspaces, I don't understand that well enough, especially \
for large teams that have overlapping workspaces"
```

`--dry-run` runs preflight and prints the image tag, whether a build is needed,
the run directory, and the full `container run` argv — then exits 0 without
building or running. It is the cheapest way to see what the real run would do.

Other options: `--workspace` and `--repo` override the mounted checkouts
(default: this repo, and the nearest ancestor declaring a workspace),
`--run-dir` overrides where the run's artifacts land, and `--cpus` (4) and
`--memory` (`8G`) size the VM.

## What a run does

1. **Preflight**, then an image build tagged `shipd-runner:<sha256(Dockerfile)[:12]>`
   — skipped when `container image list` already carries that tag, so editing
   the Dockerfile is what triggers a rebuild.
2. **`container run`** with the workspace root mounted read-only at
   `/mnt/workspace`, the repo read-only at `/mnt/repo`, and the run directory
   writable at `/out`. Tokens are passed by name (`-e GH_TOKEN`), never by
   value in the argv.
3. **Inside the VM**, `entry.py` clones the workspace to `/workspace/ws` and the
   repo beneath it at its registered workspace-relative path, repoints each
   clone's `origin` at the URL its mount carries, and sets `"pr-mode": "draft"`
   in the cloned workspace's `.shipd-config.json` — the layer that governs every
   repo beneath it, so the build stops at an open draft PR instead of enabling
   auto-merge.
4. **Two grade-gated drives** through the engine's shared session driver:
   `/s:plan` in the repo clone, graded by a worktree whose change reads
   `Status: ready` and lints clean; then `/s:build` in that worktree, graded by
   an archived change plus a PR URL from `gh pr view`.
5. **The result**: the launcher prints the PR URL on its last line and exits 0,
   or prints the failure and exits 1.

## Where the run lands

```
~/.shipd/container/runs/<UTC yyyymmddTHHMMSSZ>/
  result.json          change, pr_url, plan_session_id, build_session_id, failure
  plan-turn<N>.json    each planning turn's transcript
  build-turn<N>.json   each building turn's transcript
```

The session ids in `result.json` are resume handles: `claude --resume <id>`
reopens that exact conversation. Nothing else survives the VM — its oracle queue
writes and `~/.claude` state are discarded when the container exits.

## Runtime neutrality

`entry.py` takes its mounts, its output directory, and its clone root as
arguments and knows nothing about Apple `container`. That is deliberate: the
same script becomes an ax Task command by changing only how it is invoked.

## Tests

```
python3 -m unittest discover -s tools/tests -v
```

The suite never touches the real tool: a stub `container` script goes first on
`PATH` and logs its argv, and the entry script is driven through its injectable
turn-runner and `gh` seams, so no test builds an image or spawns a session.
