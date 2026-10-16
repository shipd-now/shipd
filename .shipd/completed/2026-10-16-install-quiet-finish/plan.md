# install-quiet-finish
Status: verified
Planned-at: 4a012c33331ad02fd531c6f8b28c0d71df8d2675
Gated-hash: 10a179775256

## Idea

Make the end of `shipd install` quiet and self-repairing: one progress line
while the checks run, the local tooling installed automatically, and a line
only for what is still wrong, each with its reason and its fix.

### Motivation

The install finish prints all eighteen preflight lines, most of them `ok`, so
the few problems drown in noise. It also tells the user to run
`/s:doctor` or `semdiff doctor --fix` for `difft`, `textual`, and the
statusline — remedies the binary already runs unattended under
`shipd doctor --fix`. A user who just ran the installer should not have to
run a second installer.

### Details

The finish shows a single terminal line, rewritten in place, naming the
check count and the check being run (`[11/18] difft`). It then installs any
missing local tooling — `difft`, `textual`, the statusline — on that same
line, and re-runs the checks it repaired. It ends with one summary line,
then one line per remaining non-`ok` check and an indented `fix:` line under
it. The `/s:doctor` pointer goes away.

### Non-goals

- The bare `shipd doctor` output and `shipd doctor --fix` stay unchanged —
  the `/s:doctor` skill parses the `ok|warn|fail` lines.
- No GitHub-side mutation: `protection` and `automerge` stay report-only.
- The drive CLI's Playwright provisioning stays out of the install.
- `install.sh` itself is unchanged.
- `README.md`'s install-finish sentence is rewritten to match, per the
  `project-readme` `harness-mode-docs` requirement (base 840c0cd19666).

## Implementation

- **Lazy check steps.** Add `check_steps(root)` to `plugins/s/bin/shipd`,
  returning the eighteen checks as an ordered list of `(name, thunk)` pairs in
  today's `default_checks` order. The GitHub context resolves lazily, once,
  on the first GitHub-side thunk, so the progress line shows real progress.
  `default_checks(root)` becomes `[thunk() for _name, thunk in
  check_steps(root)]`, so `doctor` and `doctor --fix` keep their exact output.
- **Progress line.** `doctor_finish(handle, root=None, steps=None,
  run=default_run)` writes `Checking your setup: [<i>/<n>] <name>` with a
  leading `\r` and the erase-line sequence `\033[K`, flushing per step. The
  handle is always the interactive tty (the install verb runs the finish only
  there), so no non-tty fallback is needed.
- **Automatic remedies.** For every non-`ok` result whose name is in
  `AUTOMATED_REMEDIES`, rewrite the line as `Installing: <name> …` and run
  `_remedy_argv(name, detail)` through `run`, capturing output — nothing the
  installer prints reaches the terminal. Afterwards re-run only that check's
  thunk from a fresh `check_steps(root)`. On a non-zero exit or an `OSError`,
  keep the reason: the last non-blank line of stderr (else stdout), or
  `unknown error`.
- **Final report.** Clear the line, then write
  `✓ <ok> of <n> checks ok` and, per remaining non-`ok` result in check
  order, `<level> <name> — <reason>` then `     fix: <hint>`. The reason is
  the check's detail, with ` (automatic install failed: <reason>)` appended
  when a remedy ran and failed. The hint comes from a new `FINISH_FIXES`
  table keyed by check name:
  - `difft`: `brew install difftastic` (or `cargo install difftastic`)
  - `textual`: the `pip install …` hint already composed after the detail's
    last `; `, prefixed by `python3 -m`
  - `statusline`: `shipd statusline install`
  - `protection`: `an admin of the repository runs /s:gate`
  - `automerge`: `an admin of the repository enables auto-merge (/s:doctor)`
  - `gh`: `gh auth login`
  - `local-state`: `shipd init`
  - any other name: `run /s:doctor`
- **Exit code.** Unchanged: the finish returns `None` and never alters the
  verb's exit code. The heading constant stays; `INSTALL_FINISH_POINTER` is
  deleted.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` `0.6.304` →
  `0.6.305`.

## Readiness attestation

### Problem and motivation

The install finish is noisy and hands the user remedies the binary can run.

Evidence:

- `plugins/s/bin/shipd` `doctor_finish` writes every `doctor_report` line
  and `INSTALL_FINISH_POINTER` naming `/s:doctor`.
- `check_difft` detail reads "run /s:doctor or `semdiff doctor --fix` to
  install it"; the user's pasted output shows 13 `ok` lines and 5 `warn`.

### Scope and non-goals

Only the install finish changes.

Evidence:

- In scope: `doctor_finish`, a new `check_steps`, `default_checks` rewired
  onto it.
- Out of scope: `cmd_doctor` output, `REMEDY_SURFACES`, `install.sh`,
  `install_tui.run`.

### Affected capabilities and files

One capability, one modified requirement.

Evidence:

- `install-tui`: `install-doctor-finish` (base 8de6347382d3).
- Files: `plugins/s/bin/shipd`, `plugins/s/skills/build/tests/test_shipd_cli.py`
  (`DoctorFinishTest`), `plugins/s/.claude-plugin/plugin.json`.
- `install_tui.run` calls `finish(tty)` only after a confirmed selection on a
  colour-capable tty, so the progress line always has a terminal.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Install without asking, progress on one line, a line per remaining
  problem with reason and fix: stated by the user.
- Remedy set = `AUTOMATED_REMEDIES`; GitHub-side and drive stay out:
  settled by the existing remedy boundaries.
