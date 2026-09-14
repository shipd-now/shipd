# Linter output

The skill reads this file after running `semdiff lint`, to interpret each
linter's state, weigh its findings, read the `lint` configuration key, and
understand a `failed` entry.

Run:

```
python3 "$CLAUDE_PLUGIN_ROOT/skills/review/scripts/semdiff.py" lint <base> [<head>]
```

over the same endpoints already resolved for `diff`/`files`. It emits one
JSON object: the resolved `base`/`head`/`mode`, a `linters` list, and a
`summary` carrying per-state and finding counts.

## Detection table

A linter counts as detected when its conventional marker file is present
**and** its binary resolves — checked at `node_modules/.bin/<tool>` from the
repository root, then `PATH`. A marker with no resolvable binary is reported,
never dropped.

| Linter | Marker | Binary | Machine format |
| --- | --- | --- | --- |
| `ruff` | `ruff.toml`, `.ruff.toml`, or `[tool.ruff]` in `pyproject.toml` | `ruff` | `--output-format json` |
| `flake8` | `.flake8`, or `[flake8]` in `setup.cfg`/`tox.ini` | `flake8` | `--format=json` |
| `pylint` | `.pylintrc`, or `[tool.pylint]` in `pyproject.toml` | `pylint` | `--output-format=json` |
| `eslint` | any `eslint.config.*` or `.eslintrc*` | `eslint` | `--format json` |

Each linter runs only over the changed paths whose extension it owns, and
only against a fixed argv the engine itself constructs — never a fix or write
flag. A `package.json` `lint` script is detected separately, as
`npm-lint-script`.

## The five states

- **`ran`** — the linter executed and its `findings` reflect its output.
  Read `argv` to see exactly what ran.
- **`unavailable`** — the marker is present but no binary resolved. The
  configured check did not run; say so rather than treating the area as
  clean.
- **`skipped`** — detected but owning no changed path in this diff, or
  suppressed via `lint.disable`. Never run.
- **`not-run`** — a `package.json` `lint` script was detected but
  `lint.run_scripts` is not set. The repository has not opted in.
- **`failed`** — a timeout, a crash, or output that would not parse. The
  entry carries a `stderr` excerpt; the subcommand still exits `0`, so a
  failing linter never blocks the review.

## The `lint` configuration key

`.shipd-config.json`'s `lint` key has two recognized members: `run_scripts`
(boolean, default `false`) permits executing a `package.json` `lint` script
instead of only reporting it `not-run`; `disable` (a list of linter names,
default `[]`) suppresses a detected linter regardless of its marker or
binary. Where no layer declares `lint`, both defaults apply.

## Reading a `failed` entry

Check `argv` first — it names exactly what ran, so the failure is
reproducible by hand. Then read `stderr`: a timeout excerpt names the
timeout; a crash or unparseable-output excerpt carries the tool's own error
text, truncated. Treat a `failed` linter the same as a missing one — it costs
accuracy, and the review continues without it.
