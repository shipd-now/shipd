## 1. Launcher

- [x] 1.1 [req: spike-preflight, spike-image, spike-run] Add
      `tools/tests/test_container_spike.py` with a helper that writes a stub
      `container` shell script into a temp dir (logging argv to a file;
      `system status` exits 0; `image list --quiet` prints a configurable
      tag; `run` optionally writes `result.json` into the mounted run dir),
      creates a temp workspace git repo tracking `.shipd-config.json` and a
      repo git checkout two levels beneath it (repo path shipd/shipd) with `origin` remotes and
      a git identity, and runs `tools/container/spike.py` via subprocess with a
      controlled env. Cover: missing tool exits 2 naming the releases URL and
      `container system start`; missing Claude token exits 2 naming
      `claude setup-token`; `--dry-run` prints the tag and run argv with no
      `build`/`run` logged; present tag skips build; absent tag builds once
      before run; run argv carries the three mounts, `-e GH_TOKEN`,
      `-e CLAUDE_CODE_OAUTH_TOKEN`, no `-e ANTHROPIC_API_KEY`, and
      `--repo-path` naming that relative repo path; `result.json` with `pr_url` exits 0 printing
      it last; without `pr_url` exits 1 printing the failure. Run it and
      observe every test fail because the launcher does not exist.
- [x] 1.2 [req: spike-image] Add `tools/container/Dockerfile`: `FROM
      node:22-bookworm`; `ARG CLAUDE_CODE_VERSION=2.1.284`; `ENV
      IS_SANDBOX=1`; apt install `ripgrep jq` and clean lists; `npm install -g
      @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}`; gh from
      `https://cli.github.com/packages` with `arch=arm64` and its keyring;
      difftastic from
      `https://github.com/Wilfred/difftastic/releases/download/0.71.0/difft-0.71.0-aarch64-unknown-linux-gnu.tar.gz`
      installed to `/usr/local/bin/difft`; final `RUN claude --version && gh
      --version && difft --version && python3 --version`.
- [x] 1.3 [req: spike-preflight, spike-image, spike-run] Add
      `tools/container/spike.py` (stdlib; argparse with `--dry-run`,
      `--workspace`, `--repo`, `--run-dir`, `--cpus` default 4, `--memory`
      default `8G`, positional `feedback`): preflight in the order and with the
      `Error: <what> — <remedy>` lines the plan's Implementation states, exit
      2; tag = `shipd-runner:` + sha256(Dockerfile)[:12]; build when `container
      image list --quiet` lacks the tag; run dir creation; the `container run`
      argv exactly as requirement `spike-run` lists; `--dry-run` printing tag,
      build-needed, and argv; after the run read `result.json` and exit 0
      with the URL last or 1 with the failure. Confirm the 1.1 tests pass.

## 2. Entry script

- [x] 2.1 [req: entry-clone-layout, entry-drive] Extend
      `tools/tests/test_container_spike.py` with entry-script tests that import
      `tools/container/entry.py` as a module: nested clones under a temp
      `--root` with rewritten origins; `pr-mode: draft` injected with other
      keys preserved; plan grade returns the change name for a worktree at
      `Status: ready` that lints clean (build the fixture from the
      repo's own `.shipd/README.md` grammar: `plan.md`, one delta spec, one
      tagged task); build drive follows a passed plan drive with an injected
      runner and an injected `gh` function, writing `result.json` with
      `change`, both session ids, and the URL; an exhausted plan drive records
      an empty `pr_url` and a `failure` naming `plan`. Run them and observe
      them fail.
- [x] 2.2 [req: entry-clone-layout] Add `tools/container/entry.py` (stdlib;
      argparse with `--workspace`, `--repo`, `--repo-path`, `--out`,
      `--feedback`, `--root` default `/workspace`): `clone_layout()` performing
      the two clones, origin rewrites (URLs read via `git -C <mount> remote
      get-url origin`), draft injection into `<root>/ws/.shipd-config.json`,
      and `gh auth setup-git`, with the `gh` call behind an injectable
      function.
- [x] 2.3 [req: entry-drive] In `tools/container/entry.py`, add
      `plan_grade(clone)` and `build_grade(worktree, name, gh_fn)` mirroring
      `autopilot._plan_grade`/`_build_grade`, a `make_runner(out, stage,
      claude_bin, extra_args)` that runs `session_driver.run_turn`-equivalent
      subprocess turns and writes `<out>/<stage>-turn<N>.json`, and `main()`
      that imports the engine modules from
      `<clone>/plugins/s/skills/build/scripts`, drives plan then build with
      `session_driver.drive`, `autopilot.GOAHEAD_REPLY`, `max_resumes=4`,
      `timeout=1800`, and writes `result.json`. Confirm the 2.1 tests pass.

## 3. Docs and CI

- [x] 3.1 [req: spike-preflight] Add `tools/container/README.md`:
      prerequisites (macOS 26 on Apple silicon, the signed pkg from
      `https://github.com/apple/container/releases`, `container system start`,
      `GH_TOKEN`, `claude setup-token` exported as `CLAUDE_CODE_OAUTH_TOKEN`),
      the launcher usage with the spike feedback as the worked example, where
      the run directory lands, and the note that the entry script is the
      future ax Task command.
- [x] 3.2 [req: spike-tests-ci] In `.github/workflows/ci.yml`, add a step
      `Run tools test suite` running `python3 -m unittest discover -s
      tools/tests -v` directly after the `Run eval harness test suite` step.

## 4. Verification

- [x] 4.1 [req: *] Run `python3 -m unittest discover -s tools/tests -v` and
      confirm every test passes; run `python3 tools/container/spike.py
      --dry-run "I want to learn more in the onboarding skill about how to
      configure workspaces, I don't understand that well enough, especially
      for large teams that have overlapping workspaces"` from the worktree root
      and confirm it exits 2 naming the installer when `container` is absent,
      or prints the run argv when it is installed.
- [x] 4.2 [req: spike-run] In `tools/container/spike.py`, derive `repo_path`
      from the repo's main checkout — the parent directory of `git -C <repo>
      rev-parse --git-common-dir` (resolved absolute) — relative to the
      workspace root, while `--mount` still binds `<repo>` itself at
      `/mnt/repo`. Add a test to `tools/tests/test_container_spike.py` that
      creates a linked worktree (`git worktree add .worktrees/x -b x`) of the
      fixture repo at `shipd/shipd`, runs `--dry-run` with `--repo` naming the
      worktree, and asserts `--repo-path shipd/shipd` and the worktree path in
      the `/mnt/repo` mount. Confirm the whole tools suite passes.
