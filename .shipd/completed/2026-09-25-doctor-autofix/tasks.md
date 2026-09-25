## 1. Widen the drive preflight's install scope

- [x] 1.1 [req: drive-doctor] In
      `plugins/s/skills/drive/tests/test_drive_cli.py`, replace the
      `--fix`-never-installs-vhs test with its inverse and add the
      failure case: `doctor --fix` with `vhs` absent installs it through the
      platform package manager; an install exiting non-zero reports terminal
      recording as the affected surface, names `brew install vhs`, and still
      reports every other tool. Drive both through the existing injectable
      runner seam (`default_run`) — never the real package manager. Run them
      and observe them fail.
- [x] 1.2 [req: drive-doctor] In
      `plugins/s/skills/drive/scripts/drive.py`, extend `cmd_doctor`'s
      `--fix` path to install a missing `ffmpeg`, `ffprobe`, or `vhs` through
      the injectable runner, after the existing browser install. Record each
      outcome and continue past a failure rather than returning early. Keep
      the pre-`--fix` reporting path untouched. Run task 1.1's tests until
      they pass.
- [x] 1.3 [req: drive-doctor] Make the `--fix` report name, per tool that is
      still missing after its install attempt, the surface its absence
      affects: recording and post-processing for `ffmpeg`/`ffprobe`, terminal
      recording for `vhs`, and the manual command as the remedy. Cover the
      wording in a test.

## 2. The autonomous mode in the binary

- [x] 2.1 [req: doctor-verb] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add a `DoctorFixTest`
      case asserting: bare `shipd doctor` still attempts no install and
      reaches no network; `--fix` runs a local remedy with no prompt; a
      `protection` or `automerge` finding performs no `gh api` mutation under
      `--fix` and names its affected surface; a failing remedy is reported
      and the next one still runs; `--fix` delegates to the drive CLI as its
      final step; and the exit code reflects the post-repair re-run. Drive
      every remedy through an injected runner, following the black-box style
      the file already uses. Run them and observe them fail.
- [x] 2.2 [req: doctor-verb] In `plugins/s/bin/shipd`, add a remedy table
      mapping a check name to its automated local remedy and to the surface
      its absence affects. Cover `textual`, `difft`, and `statusline` as
      automated; mark `protection`, `automerge`, `python`, `config`,
      `pipeline`, `gh`, and `copilot-secret` as report-only with their
      affected surface. Compose the `textual` command from the finding's own
      detail exactly as `doctor-remedy-boundaries` specifies, including any
      `--break-system-packages`.
- [x] 2.3 [req: doctor-verb] Add `--fix` to `cmd_doctor`'s parser and
      implement the autonomous loop: state the network access before
      performing it, run each automated remedy in check order through an
      injectable runner, record every outcome, and continue past a failure.
      Leave the bare path byte-identical in behavior.
- [x] 2.4 [req: doctor-verb] Add the delegation step: after its own
      remedies, `--fix` invokes
      `<PLUGIN_ROOT>/skills/drive/scripts/drive.py doctor --fix` as a
      subprocess and relays its report. An absent drive CLI is one more
      reported finding, never an error. Keep the binary stdlib-only — a
      subprocess, never an import.
- [x] 2.5 [req: doctor-verb] Re-run every check after the remedies and print
      that second report, exiting on its outcome. Make the rendering
      distinguish the before and after states so a reader can see what the
      run repaired. Run task 2.1's tests until they pass.
- [x] 2.6 [req: doctor-verb] Update the binary's module docstring: `doctor`
      joins the declared write exceptions under the explicit `--fix` word,
      taking the count from ten to eleven, and the verb's own `--help`
      description stops claiming "Reports only" for the flagged form.

## 3. Boundary and release

- [x] 3.1 [req: doctor-remedy-boundaries] In
      `plugins/s/skills/doctor/SKILL.md`, state that the binary's
      `doctor --fix` provisions local tooling autonomously and that the
      skill remains the only path to the two GitHub-side mutations. Leave the
      consent round and the remedy table otherwise unchanged.
- [x] 3.2 [req: doctor-remedy-boundaries] Mirror that addition in
      `plugins/s/harness/bodies/doctor.md`, keeping its one-line description
      comment in the house shape.
- [x] 3.3 [req: doctor-verb] Document the new mode in `docs/` through the
      `/s:document` skill, per the AGENTS.md rule that `docs/` prose is
      authored through that skill and lint-clean before shipping. Cover what
      `--fix` installs, what stays report-only and why, and the delegation to
      the drive preflight.
- [x] 3.4 [req: doctor-verb] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` to the next patch version, as
      the cache-snapshot rule in `AGENTS.md` requires for any change touching
      `plugins/s/`.
- [x] 3.5 [req: doctor-verb] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests`,
      `python3 -m unittest discover -s plugins/s/skills/drive/tests`, and the
      docs lint over any page task 3.3 touched, and fix anything that fails
      until all are clean.
