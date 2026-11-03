## MODIFIED Requirements

### Requirement: Sandbox leak refusal
id: sandbox-run-leak-refusal
base: 9dacf82c23a4

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
