<!-- doc-type: how-to -->

# Doctor

The doctor checks the environment shipd runs in. `shipd doctor` preflights
the environment and changes nothing. It prints one line per check, so a
broken tool or a missing setting shows up before a build trips on it.

Two layers sit on top of the preflight. `shipd doctor --fix` installs the
local tooling without asking. `/s:doctor` maps each finding to a remedy, asks
for consent, and runs only the remedies you approve.

## When to use it

- **Set up a new machine.** Run `shipd doctor --fix` to install the local
  tooling in one command.
- **Debug a failing build or gate.** Run `shipd doctor` and read the `warn`
  and `fail` lines.
- **Repair a repository's GitHub settings.** Run `/s:doctor`, the only path
  to the GitHub-side remedies.

## How to run it

### Preflight the environment

```
shipd doctor
```

The output follows a fixed contract:

- one `ok`, `warn`, or `fail` line per check, as `<level> <check> — <detail>`;
- a closing `doctor: ok` or `doctor: <n> problem(s)` line;
- exit code `1` only when a required check failed, and `0` otherwise.

### Install the local tooling

```
shipd doctor --fix
```

`--fix` installs `textual`, `difft`, and the statusline without asking. It
then installs the drive tools `ffmpeg`, `ffprobe`, and `vhs`, and re-reports.
`--fix` never changes a setting on GitHub. A `protection` or `automerge`
finding stays report-only, behind the consent of `/s:doctor`.

### Repair with consent

1. Run `/s:doctor`. The skill runs the preflight and keeps its output as the
   before state.
2. The skill maps each non-`ok` finding to a remedy, or marks it report-only.
3. The skill asks once for consent, in one batched selection over the
   runnable remedies.
4. The skill runs only the remedies you approve, one at a time.
5. The skill re-runs the preflight.
6. The skill reports the before and after states, and anything still open.

When every check is `ok`, the skill reports the result and runs no remedy.
`/s:doctor` runs one remedy round per invocation and never retries a remedy.

`/s:doctor` is the only path to the GitHub-side remedies: branch protection
and auto-merge. The consent dialog names each one with the exact change it
makes on GitHub.

Two hand-offs stay with you, because each one is interactive:

```
gh auth login
gh secret set COPILOT_GITHUB_TOKEN
```

A report-only finding has no remedy. The skill relays its line and hint.

The setup of the review gate lives on
[Copilot review](copilot-review.md).

## Reference

### Checks

| Check | What it checks |
| --- | --- |
| `python` | The interpreter the engine runs on is 3.9 or later. |
| `git` | `git` is on `PATH`. |
| `config` | The layered configuration resolves a usable content directory. |
| `pipeline` | The effective autonomous pipeline resolves. |
| `schema` | The artifact grammar version of the repository matches the engine. |
| `wiki` | The wiki store the working directory resolves. Report-only. |
| `store` | The external store the working directory resolves, if any. Report-only. |
| `store-sync` | How far the store checkout has drifted from its upstream. Report-only. |
| `local-state` | git ignores `state.json` and `autopilot/` in the content directory. Report-only. |
| `gh` | `gh` is on `PATH` and authenticated. |
| `difft` | `difft` is on `PATH`. |
| `textual` | `textual` is importable, so the delivery board can render. |
| `snapshot` | This binary is the newest installed plugin snapshot. |
| `statusline` | The shipd statusline is registered in the Claude Code settings. |
| `protection` | The default branch is protected and requires `semantic-review`. |
| `automerge` | The repository allows auto-merge. |
| `copilot-secret` | The installed review gate has its `COPILOT_GITHUB_TOKEN` secret. |
| `fast-pass` | Whether the `SHIPD_FAST_PASS` variable is on. Report-only. |
| `merge-rules` | The `shipd merge rules` ruleset exists and matches. Report-only. |
| `actions-approve` | GitHub Actions may approve pull requests, for the installed gate. Report-only. |

### Remedies on consent

| Finding | Remedy |
| --- | --- |
| `warn textual`, not importable | The `pip install` command the finding's own detail names. |
| `warn difft`, not on `PATH` | The review engine's installer for `difft`. It may reach the network. |
| `warn snapshot`, a newer version installed | `claude plugin update s@shipd`, applied in a new session. |
| `warn statusline`, not registered | [`shipd statusline install`](statusline-and-telemetry.md), shown in a new session. |
| `warn gh`, not on `PATH` | The platform's install command, such as `brew install gh`. |
| `fail git`, not on `PATH` | The platform's install command, such as `brew install git`. |
| `warn protection`, branch not protected | A minimal protection that requires `semantic-review`. |
| `warn protection`, `semantic-review` missing | Appends `semantic-review` to the required checks. |
| `warn automerge`, auto-merge disabled | Allows auto-merge on the repository. |

A finding that names a missing admin permission is report-only.

### Related pages

- [Statusline and telemetry](statusline-and-telemetry.md) covers the
  statusline that the `statusline` check reports.
- [Customising shipd](customise.md) owns the configuration that the `config`
  and `pipeline` checks read.
