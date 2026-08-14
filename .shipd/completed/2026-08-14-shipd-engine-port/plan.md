# shipd-engine-port
Status: verified
Epic: shipd-port
Theme: spec-engine

## Idea

Run the port tool to land `plugins/s/` and the root infrastructure in the shipd
repo, with every namespace constant rewritten and all four test suites green in
shipd's own CI.

### Motivation

The spec engine is where the `am` namespace is actually encoded — `CONFIG_FILENAME`,
`DEFAULT_DIR`, `DEFAULT_MEMORY_DIR`, the build log dir, the tui venv cache, the
worktree idle env var — so nothing else can be ported until the engine parses the
new names (`.shipd/epics/shipd-port/epic.md`, Design seam 2). Content is only
readable by the engine that reads it.

### Details

- Run `port.py apply --include plugins/s/ --include requirements.txt` against
  shipd at a pinned ref, landing `plugins/s/` in the shipd repo.
- Verify each namespace constant carries its `shipd` value rather than trusting
  the map.
- Add shipd's `.github/workflows/ci.yml`, retargeted at the new suite paths.
- Confirm all four suites pass under the ported paths.

Affected capabilities: `shipd-port` (added). Impact: the shipd repo
(`plugins/s/`, `requirements.txt`, `.github/workflows/ci.yml`); shipd unchanged.

### Non-goals

- No spec library. `.shipd/` is member 3's scope; this member ports code only.
- No plugin or marketplace manifest identity — `plugins/s/.claude-plugin/` lands
  as the tool wrote it and is corrected in member 4.
- No brand or documentation copy; member 5 owns that.
- No behavior change of any kind. A bug found during the port is reported, not
  fixed here.

## Implementation

- **The port runs at a pinned ref, recorded in the commit message.** `apply` is
  invoked with an explicit `--ref <sha>` rather than `HEAD`, and that sha goes in
  the PR body, so the ported tree is traceable to an exact shipd commit.
  Rejected: `HEAD` — shipd keeps moving, and an untraceable port cannot be
  re-derived or diffed.

- **Constants are verified individually, not inferred from a clean tool run.** The
  residual scan proves no `am` token survived; it does not prove the *right*
  value landed. Each of these is asserted explicitly in the ported tree:
  | file | constant | required value |
  | --- | --- | --- |
  | `plugins/s/skills/build/scripts/spec_common.py` | `CONFIG_FILENAME` | `.shipd-config.json` |
  | `plugins/s/skills/build/scripts/spec_common.py` | `DEFAULT_DIR` | `.shipd` |
  | `plugins/s/skills/build/scripts/spec_common.py` | `DEFAULT_MEMORY_DIR` | `~/.shipd-memory` |
  | `plugins/s/skills/build/scripts/build_report.py` | `log_dir` default | `~/.shipd/builds` |
  | `plugins/s/skills/build/scripts/metrics.py` | `DEFAULT_LOG_DIR` | `~/.shipd/builds` |
  | `plugins/s/skills/build/scripts/tui_bootstrap.py` | venv cache | `shipd/tui-venv` |
  | `plugins/s/skills/build/scripts/worktree.sh` | idle env var | `SHIPD_WORKTREE_IDLE_MINUTES` |
  | `plugins/s/skills/review/scripts/semdiff.py` | content-dir cohort | `.shipd` |

- **CI is authored, not ported blind.** shipd's `ci.yml` hardcodes
  `plugins/s/skills/...` discovery paths and a `.shipd/planned/*/` lint loop. The
  tool rewrites those strings correctly, but the workflow is short and
  load-bearing enough to read end to end and confirm each of the four suites plus
  both lint steps points at a path that exists in shipd.

- **Green CI is the acceptance bar.** The suites exercise the very constants the
  port rewrote — `test_spec_common.py` asserts the config filename, the
  build-report tests assert the log dir is not `~/.shipd/`. A member is done
  when they pass under the new paths, not when the diff looks right.

- **The lint steps will fail until member 3 lands, and that is expected.**
  `spec_lint.py` with no argument lints the master library, which does not exist
  in shipd yet. Those two CI steps are added in this member but the workflow is
  only required to be green from member 3 onward; this member's bar is the four
  unittest suites. This is stated in the PR body so a red lint step is not
  mistaken for a broken port.

- **The `.shipd` → `.shipd` collision is resolved by repurposing the guard against
  the legacy namespace.** In shipd the product name and the content directory are
  *different* strings (`.shipd` vs `.am`), so `test_no_shipd_path_read_or_written`
  could assert the build log never lands in a brand-named sibling of the real default.
  In shipd they are the same string, so the rename collapses both literals onto
  `.shipd` and the ported assertion ("`~/.shipd` never exists after writing a log
  entry") contradicts the required default `~/.shipd/builds`. The test keeps its
  intent — *the log never lands in a wrong-namespace path* — by asserting against the
  only wrong namespace that still exists in shipd: neither `~/.am` nor `~/.shipd`
  is created. It is renamed `test_no_am_path_read_or_written`, and the two docstrings
  that state the same invariant (`build_report.write_log_entry`, `BuildConfigTest`)
  are corrected to match. Rejected: deleting the test — the invariant is more
  load-bearing in a port than it was at home, since a missed rewrite is exactly how
  the old paths would come back.

- **Residual findings outside the constants table are reported, not fixed.**
  `port.py apply` exits `2` on this tree with residuals under `plugins/s/`:
  `AM_FLOW_LOG_DIR` in `metrics.py` and the suites that set it, and bare
  `am:<skill>` references in skill prose. Neither is in the requirement's
  enumerated pattern set or the constants table above, both are internally
  consistent (so the suites pass), and the epic's non-goal is explicit that a
  member files a defect rather than fixing it. They are map gaps in member 1's
  `tools/port.py` and are carried into the PR body as follow-up work. The binding
  no-residual gate for this member is therefore the four-pattern check, not the
  tool's exit code. Rejected: widening the map here — it would mean editing
  member 1's shipped tool and re-running the whole port, a scope change this
  member is not the place for.

Risk: `tests_textual` needs the pinned `textual` from `requirements.txt`, which is
why that file is in this member's `--include` set rather than member 5's brand
scope.
