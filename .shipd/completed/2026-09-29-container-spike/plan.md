# container-spike
Status: verified

## Idea

Add a host launcher and a runtime-neutral entry script that load the shipd
workspace and repo into an Apple `container` VM, drive headless `/s:plan` and
`/s:build` sessions on a piece of user feedback, and end on a draft PR.

### Motivation

A maintainer who receives user feedback cannot hand it to an agent that plans
and builds it unattended in a safe, self-contained runtime: every autonomous
path runs on the host, and the only sandbox (`~/.claude/skills/ax-claude`) needs
a remote cluster and x86_64 images. This spike proves the local path end to end.

### Details

- `tools/container/Dockerfile`: a Linux arm64 image with Claude Code, gh,
  difftastic, python3, git, ripgrep, and jq, derived from the axel
  `claude-runner` Dockerfile.
- `tools/container/spike.py`: the host launcher. Preflight, image build by
  Dockerfile hash, `container run` with read-only mounts of the workspace root
  and the repo, env passthrough, a run directory, `--dry-run`.
- `tools/container/entry.py`: runs inside the VM. Clones the workspace repo,
  nests a repo clone beneath it, injects `pr-mode: draft`, drives two
  grade-gated sessions through the shared session driver, writes
  `result.json`.
- `tools/container/README.md`, `tools/tests/test_container_spike.py`, and a
  CI step running `tools/tests`.

Affected capabilities: `container-spike` (new). Impact: `tools/container/`
(new), `tools/tests/test_container_spike.py` (new),
`.github/workflows/ci.yml`; no plugin change, no version bump.

### Non-goals

- No plugin skill, harness body, doctor check, or pipeline stage.
- No ax runtime; the entry script is shaped to become an ax Task command later.
- No installation of the `container` tool: preflight reports its absence.
- No retention of the VM's oracle queue writes or `~/.claude` transcripts
  beyond the per-turn JSON the entry script copies out.
- No `docs/` page.

## Implementation

- **Host tooling under `tools/`, Python stdlib only, tested by subprocess**,
  mirroring `tools/port.py` and `tools/tests/test_port.py`. Rejected: a plugin
  skill, which costs a `SKILL.md`, a harness body, and a version bump.
- **Clone from read-only mounts, never mount the checkout writable.** The
  launcher mounts the workspace root at `/mnt/workspace` and the repo at
  `/mnt/repo`, both `readonly`, plus the run directory at `/out`. The entry
  script clones the workspace to `/workspace/ws`, then the repo to
  `/workspace/ws/<repo-path>` (`<repo-path>` is the repo's main checkout,
  the parent of `git rev-parse --git-common-dir`, relative to the workspace
  root, here `shipd/shipd`, so a launcher run from a change worktree still
  nests the clone at the registered member path while cloning that
  worktree's branch), and sets each clone's `origin` to the URL read from
  the mount. Rejected: a writable mount, which would write
  Linux paths into worktree gitdir files on the host.
- **Draft mode is injected into the cloned workspace config** by setting
  `"pr-mode": "draft"` in `/workspace/ws/.shipd-config.json`. Verified: a
  parent-layer `pr-mode` governs the repo beneath it. The oracle inside the VM
  reads the cloned wiki (Q2).
- **Two drives through `session_driver.drive`**, importing `session_driver`,
  `spec_common`, `spec_status`, `spec_lint`, and `autopilot` from the clone's
  `plugins/s/skills/build/scripts`. Plan drive: cwd = clone root, the
  `/s:plan` prompt in requirement `entry-drive`, graded by a `.worktrees/<name>`
  whose change reads `ready` and lints clean. Build drive: cwd = that
  worktree, the `/s:build` draft-mode prompt, graded by an archived
  `completed/*-<name>` plus `gh pr view change/<name> --json url -q .url`.
  Reply `autopilot.GOAHEAD_REPLY`, four resumes, 1800 s per turn, mirroring
  `autopilot.py:319-342` and `:695`. Rejected: a second driving idiom.
- **Headless flags** per `evals/run.py:289-291`: `--plugin-dir
  <clone>/plugins/s --permission-mode bypassPermissions --output-format json`.
  The VM process runs as root, so the image sets `ENV IS_SANDBOX=1`, which lets
  Claude Code accept bypass mode as root; the ax notes record the refusal
  without it. Risk: a newer CLI still refusing; fallback is `USER node`.
- **Image**: `FROM node:22-bookworm`; `ARG CLAUDE_CODE_VERSION=2.1.284`; gh
  from the GitHub apt repo for `arm64`; difftastic pinned to the verified
  `difft-0.71.0-aarch64-unknown-linux-gnu.tar.gz`; `ripgrep`, `jq`; no shipd
  installer, no textual. Tag `shipd-runner:<sha256(Dockerfile)[:12]>`, built
  only when `container image list --quiet` lacks it. Rejected: `--build-arg`,
  unverified on this CLI; a version change edits the ARG default and re-tags.
- **Auth by env passthrough only**: `GH_TOKEN` plus `CLAUDE_CODE_OAUTH_TOKEN`
  or `ANTHROPIC_API_KEY`, each set name passed as `-e NAME`; git identity from
  the host `git config` as the four `GIT_*` variables; `gh auth setup-git`
  inside the VM. Preflight failures print `Error: <what> — <remedy>` and exit
  2, naming `https://github.com/apple/container/releases` and `container
  system start` for the tool and `claude setup-token` for the token.
- **Run directory** `~/.shipd/container/runs/<UTC stamp>/` (or `--run-dir`)
  holding `result.json` and the turn transcripts. Tests stub `container` with
  a shell script on PATH that logs its argv.
- **Precedent**: `/home/debian/claude-runner/Dockerfile` on axel, read
  2026-09-29, is the image's starting point.

## Questions and answers

### Q1: Where does the spike live?
- **Question:** Host tooling under `tools/container/` with no plugin bump, or
  a plugin skill under `plugins/s/skills/container/` with a version bump?
  Options: (1) tools; (2) skill. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1, `tools/container/`, for the spike. The queue entry was
  discarded as change-scoped.
- **Queued:** q-container-spike-runner-placement

### Q2: Clone the workspace repo too, or the shipd repo alone?
- **Question:** Clone the workspace repository and nest the shipd clone at its
  registered `shipd/shipd` path so the oracle reads the wiki and draft mode
  rides the workspace layer, or clone the repo alone with a synthetic parent
  config? Options: (1) nested clones; (2) repo alone. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. A workspace is bootstrapped on a fresh machine by
  cloning it and materializing members beneath it; headless sessions must
  consult the oracle rather than a human, which an amnesiac oracle cannot
  satisfy; `pr-mode: draft` belongs in the cloned workspace layer. Lost
  in-container queue writes are the accepted cost.
- **Cited:** epic/portable-workspaces, verified/shipd-workspace,
  verified/epic-autopilot, verified/shipd-config

## Readiness attestation

### Problem and motivation

Feedback cannot be handed to an agent that plans, builds, and opens a draft PR
unattended in an isolated local runtime.

Evidence:

- `~/.claude/skills/ax-claude/SKILL.md` lines 1-12: the only sandbox is a
  remote gVisor cluster with an x86_64 image.
- Capability `epic-autopilot` drives sessions on the host; `autopilot.py:695`
  sets each session's cwd to a host worktree.

### Scope and non-goals

The change adds host tooling under `tools/` and one CI step; the plugin, the
doctor, the pipeline, and the ax runtime are untouched.

Evidence:

- In scope: `tools/container/` (new), `tools/tests/` (new file),
  `.github/workflows/ci.yml:32-33` (a step after the eval suite).
- Out of scope: `plugins/s/` is not edited, so `AGENTS.md:16-19`'s version
  bump rule does not apply.

### Affected capabilities and files

One new capability and six files: the launcher, the entry script, the image,
their tests, the README, and the CI step.

Evidence:

- Capability `container-spike` (new).
- Files: `tools/container/Dockerfile`, `tools/container/spike.py`,
  `tools/container/entry.py`, `tools/container/README.md`,
  `tools/tests/test_container_spike.py`, `.github/workflows/ci.yml`.
- Runnable premise: `spec_status.py --root <scratch>/ws/repo config-show`
  with `{"pr-mode": "draft"}` in `<scratch>/ws/.shipd-config.json` printed
  `pr-mode = "draft"` with the parent file as provenance, exit 0.
- Runnable premise: `python3 -m unittest discover -s tools/tests` ran 25
  tests, OK, exit 0.
- Runnable premise: `gh api repos/Wilfred/difftastic/releases/tags/0.71.0`
  listed `difft-0.71.0-aarch64-unknown-linux-gnu.tar.gz`; `npm view
  @anthropic-ai/claude-code version` printed 2.1.284.
- Runnable premise: `gh api repos/apple/container/releases/latest` printed
  tag 1.4.1 and asset `container-1.4.1-installer-signed.pkg`; `which
  container` found nothing on this host.
- `session_driver.py:119` `drive()`, `autopilot.py:69` `GOAHEAD_REPLY`,
  `autopilot.py:319` and `:330` grades, `evals/run.py:289-291` headless flags.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Placement under `tools/`: settled by the user, Q1.
- Nested workspace clone and draft injection point: settled by the oracle, Q2.
- Read-only mounts with in-VM clones, image contents and tagging, env
  passthrough auth, root with `IS_SANDBOX=1`, two drives reusing autopilot's
  reply and grades, entry script split from the launcher: settled by
  investigation and recorded above.
