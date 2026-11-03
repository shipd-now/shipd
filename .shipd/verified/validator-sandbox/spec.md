# validator-sandbox

### Requirement: Sandbox execution entry point
id: sandbox-run-entry-point

The plugin SHALL bundle `plugins/s/skills/build/scripts/sandbox-run.sh`, a
bash shim that execs the stdlib-only `sandbox_run.py`. Given exactly one
positional command string, the wrapper SHALL run it as `bash -c` under a
sandbox env. That env SHALL set `HOME`, the four `XDG_*_HOME` variables,
`GH_CONFIG_DIR`, `GIT_CONFIG_GLOBAL` and `TMPDIR` under a per-repo sandbox
root, and SHALL set `GIT_CONFIG_NOSYSTEM=1`, `SHIPD_SANDBOX=1` and
`SHIPD_SANDBOX_ROOT`. The wrapper SHALL unset `GH_TOKEN`, `GITHUB_TOKEN`,
`GH_ENTERPRISE_TOKEN` and `GITHUB_ENTERPRISE_TOKEN`, and SHALL propagate the
command's exit status. The sandbox root SHALL be
`<tmp>/shipd-sandbox/<first 12 hex of sha256(repo root)>`, and it SHALL
persist across calls until `--reset` removes it. The wrapper SHALL print
`sandbox-run: root=<root>` as its first stderr line. If it cannot create the
root, or the root resolves inside the real HOME, it SHALL exit 3 with a
message naming the path and run nothing.

#### Scenario: A home write lands in the sandbox
- **GIVEN** a temp directory standing in for the real HOME, with a sentinel
  file at `<home>/.review-bot/config.json`
- **WHEN** `sandbox-run.sh 'mkdir -p ~/.review-bot && echo sandboxed > ~/.review-bot/config.json'`
  runs with that HOME
- **THEN** it exits 0, `<root>/home/.review-bot/config.json` holds `sandboxed`,
  and the sentinel file is byte-identical to before

#### Scenario: The banner names the root
- **WHEN** any command runs through the wrapper
- **THEN** the first stderr line is `sandbox-run: root=<root>` and
  `SHIPD_SANDBOX` is `1` inside the command

#### Scenario: GitHub credentials do not reach the command
- **GIVEN** `GH_TOKEN` and `GITHUB_TOKEN` set in the caller's env
- **WHEN** the wrapper runs `env`
- **THEN** neither variable appears in the output, and `GH_CONFIG_DIR` points
  under the sandbox root

#### Scenario: An uncreatable root fails loudly
- **GIVEN** the temp directory resolves to a path where the root cannot be
  created
- **WHEN** the wrapper runs a command
- **THEN** it exits 3, stderr names the path, and the command does not run

#### Scenario: State persists until reset
- **WHEN** one call writes `~/x` and a second call reads it, then
  `sandbox-run.sh --reset` runs and a third call reads it
- **THEN** the second read succeeds and the third finds no file

### Requirement: Sandbox leak refusal
id: sandbox-run-leak-refusal

The wrapper SHALL accept the command only as one positional string, and SHALL
exit 2 with `sandbox-run: pass the command as one quoted string` on zero or
several positionals. If the command string names the real HOME path anywhere
the continuation does not begin with a form of the repo-root path, then the
wrapper SHALL exit 2 without running it. The forms of the repo root SHALL be
its resolved path and, when it sits under the real HOME, its path under each
form of the real HOME (the literal value and the resolved value). The wrapper
SHALL drop every inherited variable except `PATH` and the toolchain locators
`PYENV_ROOT`, `RBENV_ROOT`, `ASDF_DATA_DIR`, `VIRTUAL_ENV` and `CONDA_PREFIX`
whose value names the real HOME outside the repo root. When `PYENV_ROOT`,
`RBENV_ROOT` or `ASDF_DATA_DIR` is unset and `PATH` holds
`<real-home>/.pyenv/shims`, `<real-home>/.rbenv/shims` or
`<real-home>/.asdf/shims` respectively, the wrapper SHALL set that variable to
the shim directory's parent.

#### Scenario: A pre-expanded home path is refused
- **WHEN** the command string contains `<real-home>/.review-bot/config.json`
- **THEN** the wrapper exits 2, stderr names the match, and nothing is written

#### Scenario: A repo path under home is allowed
- **GIVEN** a repo root inside the real HOME
- **WHEN** the command string names `<repo-root>/scripts/tool.sh`
- **THEN** the wrapper runs the command

#### Scenario: A repo path through a symlinked home is allowed
- **GIVEN** a real HOME given as a symlink whose target holds the repo
- **WHEN** the command string names the repo through the symlinked HOME path
- **THEN** the wrapper runs the command

#### Scenario: Unquoted argv is refused
- **WHEN** the wrapper receives two positional arguments
- **THEN** it exits 2 with the one-quoted-string message

#### Scenario: A home-pointing state var is scrubbed
- **GIVEN** `REVIEW_BOT_HOME=<real-home>/.review-bot` in the caller's env and no
  `sandbox.env` entry for it
- **WHEN** the wrapper runs `env`
- **THEN** `REVIEW_BOT_HOME` is absent from the output

#### Scenario: A pyenv shim still resolves
- **GIVEN** `PATH` starting with `<real-home>/.pyenv/shims`, a shim there that
  execs `${PYENV_ROOT:-$HOME/.pyenv}/versions/x/bin/python3`, and
  `PYENV_ROOT=<real-home>/.pyenv`
- **WHEN** the wrapper runs `python3 -c 'print(42)'`
- **THEN** it prints `42`, and `HOME` inside the command is still the sandbox HOME

#### Scenario: An unset pyenv root is derived from the shim path
- **GIVEN** the same shim on `PATH` and no `PYENV_ROOT` in the caller's env
- **WHEN** the wrapper runs `echo $PYENV_ROOT`
- **THEN** it prints `<real-home>/.pyenv`

### Requirement: Project sandbox declaration
id: sandbox-run-project-config

Where the resolved configuration declares `sandbox.env`, the wrapper SHALL set
each named variable to `<root>/state/<path>` and create its parent directory.
Where it declares `sandbox.fake_bin`, the wrapper SHALL prepend
`<repo-root>/<fake_bin>` to `PATH`. If the declared `fake_bin` does not exist,
then the wrapper SHALL exit 3 naming it and run nothing.

#### Scenario: Declared state var points into the sandbox
- **GIVEN** `"sandbox": {"env": {"REVIEW_BOT_HOME": "review-bot"}}`
- **WHEN** the wrapper runs `echo $REVIEW_BOT_HOME`
- **THEN** it prints `<root>/state/review-bot`

#### Scenario: Fake bin shadows the real tool
- **GIVEN** `"sandbox": {"fake_bin": "tests/fake-bin"}` with an executable
  `tests/fake-bin/gh` that prints `fake-gh`
- **WHEN** the wrapper runs `gh api user`
- **THEN** it prints `fake-gh`

#### Scenario: Missing fake bin fails loudly
- **GIVEN** `sandbox.fake_bin` names a directory that does not exist
- **WHEN** the wrapper runs a command
- **THEN** it exits 3 naming the directory

### Requirement: Agent sandbox contract
id: agent-sandbox-contract

`plugins/s/agents/validator.md` SHALL carry a `## Sandbox` section. That
section SHALL require every Bash command that runs `gh`, `git`, a project
script, a test, or anything that reads or writes state to go through
`bash <SANDBOX_RUN> '<command>'`, and SHALL name a raw call a contract
violation. Bare Bash SHALL stay allowed only for read-only file listing and
reading, with the Read and Grep tools direct. `plugins/s/agents/sub-agent.md`
SHALL require the same wrapper for tasks that exercise `gh`, git remotes or
watcher scripts against fakes. Each `plugins/s/harness/agents/` twin SHALL
carry a body identical to its agent definition.

#### Scenario: Validator contract names the wrapper
- **WHEN** `validator.md` is read
- **THEN** its `## Sandbox` section names `<SANDBOX_RUN>`, the one-quoted-string
  form, and calls a raw `gh`/`git`/script call a contract violation

#### Scenario: Harness twins stay in step
- **WHEN** each agent definition's body is compared with its `harness/agents/`
  twin's body
- **THEN** the two are identical
