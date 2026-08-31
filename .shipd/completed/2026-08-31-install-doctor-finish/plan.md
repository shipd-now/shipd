# install-doctor-finish
Status: verified
Theme: developer-experience

## Idea

Close the interactive `shipd install` finish with the read-only `shipd doctor`
preflight, printed on the same terminal the harness picker reported on.

### Motivation

`install.sh` ends a fresh install by telling the user `Then run: shipd doctor`
and then hands the terminal to the harness picker, which stops at its
per-harness report — so the one preflight that would catch a broken new
environment is left to the user to remember. Running it where the picker
already owns the terminal makes the first install self-verifying.

### Details

- Give `install_tui.run`/`main` an optional `finish` callable, invoked with the
  terminal handle once a confirmed selection has been recorded and reported.
- Add `doctor_finish()` to `plugins/s/bin/shipd`, composing the existing
  `default_checks()` and `doctor_report()`, and pass it from `cmd_install`.
- Document the new closing step in the README's install finish paragraph.
- Bump the plugin version (`plugins/s/.claude-plugin/plugin.json`).

Affected capabilities: `install-tui` (modified), `project-readme` (modified).
Impact: `plugins/s/skills/build/scripts/install_tui.py`, `plugins/s/bin/shipd`,
`README.md`, `plugins/s/skills/build/tests/test_install_tui.py`,
`plugins/s/skills/build/tests/test_shipd_cli.py`. No new dependencies — the
preflight is the one already in the binary.

### Non-goals

- No change to `install.sh` — its `Then run: shipd doctor` line stays correct
  for the headless path, where the picker never runs.
- No change to the `shipd doctor` verb, its checks, or its output grammar.
- No remedies: the finish reports, exactly as `shipd doctor` does. Fixing
  findings stays `/s:doctor`'s job.
- No new flag to suppress the preflight.

## Implementation

- **The composition lives in `cmd_install` (`plugins/s/bin/shipd:1979`), not in
  `install_tui`.** The checks are defined in `bin/shipd`, which has no `.py`
  suffix and is importable only through an explicit `SourceFileLoader` (as
  `plugins/s/skills/build/tests/test_shipd_cli.py:48` does); making the engine
  script import the binary would invert the dependency. Rejected: moving the
  checks into a new engine module — a far larger change than the request, and
  it would drag `shipd-cli`'s `doctor-verb` requirement along.
- **`install_tui.run(tty=None, out=None, finish=None)` and
  `main(argv=None, finish=None)`.** `finish` is called as `finish(tty)` with
  the same handle `install_selection` reported on, so the preflight lands on
  `/dev/tty` like the rest of the flow — under `curl | sh` stdout is that tty
  anyway, but `shipd install > log` must not split the output. Default `None`
  keeps every existing caller and test unchanged. Rejected: returning a richer
  result from `run` for the caller to branch on — it would break the
  "return the exit code" convention `cmd_install` relies on.
- **Called on the confirmed paths only**, after the record is saved: both when
  harnesses were generated and when the user confirmed an empty selection
  (they are equally "finished adjusting"). Not called on abort, not on the
  headless degradation, and not when `install_selection` returns a refusal
  reason — `install-tui`'s `install-verb` requirement pins the first two as
  write-nothing/output-unchanged, and the third is an error exit.
- **The preflight's verdict never changes the verb's exit code.** `install.sh`
  reports any nonzero from `shipd install` as
  `Note: skipped the harness picker`, so a `fail python` would make the
  installer claim the picker never ran. Verified by running
  `plugins/s/skills/build/tests/test_install.py` (`Ran 20 tests … OK`), whose
  `test_a_failing_interactive_finish_never_fails_the_installer` pins that note.
  `doctor_finish` therefore discards `doctor_report`'s exit code.
- **Output shape.** A blank line, the heading constant, a blank line — written
  and flushed *before* the checks run, because the GitHub-side probes take a
  few seconds (`plugins/s/bin/shipd doctor` measured at 3.8s in a `gh`-authed
  repo, `doctor: ok`, exit 0). Then `doctor_report`'s lines verbatim, and —
  only when some check is not `ok` — a blank line and one pointer line naming
  `/s:doctor`. Two module constants in `bin/shipd` hold the heading and the
  pointer.
- **Injection for tests.** `doctor_finish(handle, root=None, checks=None)`
  defaults `checks` to `default_checks` and `root` to `os.getcwd()`, so the
  suite drives it with fabricated results and never reads the ambient
  environment — the same seam style the existing doctor tests use.

Risk: the preflight adds a few seconds to a `curl | sh` install where the
working directory happens to be a GitHub repository. Accepted — the checks
self-skip outside one (`gh_context` returns `skip`), and the heading is
flushed first so the pause is explained.
