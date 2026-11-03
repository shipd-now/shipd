# sandbox-followups
Status: verified

## Idea

Close the three loose ends the `validator-sandbox-run` build (PR #408) left: a path-sensitive autopilot test, a spurious leak refusal under symlinked paths, and pyenv-style shims that break inside the sandbox.

### Motivation

- `test_autopilot`'s `test_bare_entries_keep_todays_prompts` fails whenever the checkout path contains "validator", because the build prompt embeds the plugin script path.
- The leak check compares the repo root only in its resolved form. A command naming the repo through a symlinked HOME (macOS `/var` vs `/private/var`) is refused although it stays inside the repo.
- A probe with a pyenv-style shim on `PATH` and `PYENV_ROOT=<home>/.pyenv` showed `python3` exit 126 inside the sandbox: the scrub drops `PYENV_ROOT`, so the shim looks under the sandbox HOME.

### Details

- `plugins/s/skills/build/tests/test_autopilot.py`: assert on the prompt with its path-bearing constants removed.
- `plugins/s/skills/build/scripts/sandbox_run.py`: accept every home form of the repo root, and keep named toolchain locator variables.
- Tests in `plugins/s/skills/build/tests/test_sandbox_run.py`; version bump.

Affected capabilities: `validator-sandbox`.

### Non-goals

- No generic "keep vars whose path is on `PATH`" rule: `~/.local/bin` on `PATH` would then keep a var pointing at `~/.local`, a leak.
- No detection of an un-resolved alias of a real HOME that has no symlink in its own form.
- No change to `mise` handling: its installs sit on `PATH` directly and resolve today.

## Implementation

**Autopilot test.** In `test_bare_entries_keep_todays_prompts`, build `text` from each prompt with `autopilot.ORACLE_LOOKUP_CMD` and `autopilot.ORACLE_JUDGE_NOTE` replaced by `""`, then run the existing `assertNotIn` checks on `text` (lowercased where they lowercase today). The two `assertEqual` checks stay on the raw prompts. Rejected: renaming the token, because the test pins the absence of a validator option line.

**Repo forms.** `main` computes `repo_forms`: the resolved repo root first, then, when the resolved root equals or sits under `os.path.realpath(real_home)`, each home form from `home_forms` joined with the root's suffix below the resolved home. Duplicates are dropped. `_is_repo_ref(text, start, repo_forms)` returns true when any form matches at `start` with the existing boundary rule. `outside_repo_home_ref(text, forms, repo_forms)` passes the list through. The command check and the env scrub both use it.

**Toolchain locators.** A module constant `TOOLCHAIN_VARS = ("PYENV_ROOT", "RBENV_ROOT", "ASDF_DATA_DIR", "VIRTUAL_ENV", "CONDA_PREFIX")` names variables the scrub keeps even when they name the real HOME. A second constant `SHIM_ROOTS = {"PYENV_ROOT": ".pyenv", "RBENV_ROOT": ".rbenv", "ASDF_DATA_DIR": ".asdf"}` covers the unset case. For each entry absent from the inherited env, when some `PATH` entry equals `<form>/<dir>/shims` for a home form, the wrapper sets the variable to `<form>/<dir>`. Both run before the sandbox `env.update`, so an explicit `sandbox.env` entry still wins.

**Risk.** A kept locator lets a toolchain install write under the real HOME, for example `pip install` into a pyenv version. `PATH` already exposes those interpreters, so this adds no new write channel; HOME, XDG and gh/git config stay redirected.
