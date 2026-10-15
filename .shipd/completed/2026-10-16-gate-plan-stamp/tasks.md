## 1. Header grammar and stamp helpers

- [x] 1.1 [req: plan-header-metadata-lines] In
      `plugins/s/skills/build/tests/test_spec_common.py`, next to the existing
      `parse_plan_metadata` tests (line 276), add tests: a header
      `Status: ready` / `Epic: e` / `Planned-at: <40 hex>` /
      `Gated-hash: <12 hex>` parses to three pairs in order; `STAMP_KEYS ==
      ("Planned-at", "Gated-hash")` and both keys are in `METADATA_KEYS`;
      `read_plan_stamp` returns both values, and `(None, None)` on an
      unstamped plan; `write_plan_stamp` appends both lines after `Epic:` on a
      plan with a block, directly after `Status:` on a plan without one,
      replaces existing stamp lines in place, and with `planned_at=None`
      writes no `Planned-at` line and removes a stale one; `plan_gated_hash`
      is unchanged by the `Status:` value, by stamp lines, and by trailing
      spaces plus doubled blank lines, and changes when `## Idea` text
      changes. Run `python3 -m unittest
      plugins.s.skills.build.tests.test_spec_common` and observe the failures.
- [x] 1.2 [req: plan-header-metadata-lines] In
      `plugins/s/skills/build/scripts/spec_common.py`: widen
      `METADATA_LINE_RE` to `^([A-Za-z][A-Za-z0-9-]*):\s*(.*?)\s*$`; add
      `STAMP_KEYS`, `PLANNED_AT_RE = ^[0-9a-f]{7,40}$`, `GATED_HASH_RE =
      ^[0-9a-f]{12}$` (built from `HASH_LENGTH`); extend `METADATA_KEYS` with
      the two stamp keys and update its comment; add `read_plan_stamp(text)`,
      `plan_gated_hash(text)` (drop the first `Status:` line and every
      header-block stamp line, return `content_hash` of the remainder), and
      `write_plan_stamp(text, planned_at, gated_hash)` placed after
      `parse_plan_metadata`, each with a docstring citing the plan-stamp
      requirement. Re-run the suite from 1.1 until it passes.
- [x] 1.3 [req: plan-stamp-write] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next patch above the
      value on `main` at build time (`0.6.293` when this plan was revised;
      rebase and re-bump if a sibling member landed first).

## 2. Lint recognition

- [x] 2.1 [req: plan-metadata-validation] In
      `plugins/s/skills/build/tests/test_spec_lint.py` `PlanMetadataTest`
      (line 494), add tests: a header with `Epic: e`, a 40-hex `Planned-at`,
      and a 12-hex `Gated-hash` lints clean; `Gated-hash: not-a-hash` errors
      naming `not-a-hash` and `hex`; `Planned-at: 123456` (six chars) errors
      naming the value; a `Planned-at` line in an epic header is still an
      unrecognized key under `_check_epic_metadata`. Run
      `python3 -m unittest plugins.s.skills.build.tests.test_spec_lint` and
      observe the failures.
- [x] 2.2 [req: plan-metadata-validation] In
      `plugins/s/skills/build/scripts/spec_lint.py` `check_plan_metadata`,
      before the `KEBAB_RE` test, validate a `STAMP_KEYS` key against its own
      regex (`PLANNED_AT_RE` / `GATED_HASH_RE`) with errors "plan.md
      `Planned-at: <v>` is not a 7–40 character lowercase hex commit id" and
      "plan.md `Gated-hash: <v>` is not a 12-character lowercase hex content
      hash", then `continue`; update the function docstring. Re-run until 2.1
      passes.

## 3. Gate writes the stamp on pass

- [x] 3.1 [req: plan-stamp-write] In
      `plugins/s/skills/build/tests/test_spec_gate.py`, add an `_init_git`
      helper on `SpecGateTestBase` mirroring
      `plugins/s/skills/build/tests/test_spec_status.py:4738-4743` but using
      `git init -q -b main` and committing the fixture, so `main` exists and
      equals `HEAD`. Add a `StampTest` class: a clean draft with `Epic: e`
      (and an `<tmp>/epics/e/epic.md` fixture, or omit `Epic:` and use `Theme:`
      with no config) in a git root passes with the header order `Status:
      ready`, `Theme: ...`, `Planned-at: <rev-parse main>`, `Gated-hash:
      <12 hex>` and stdout carrying `stamp: Planned-at`; re-gating after
      editing `## Idea` leaves exactly one line per key with a changed hash;
      a non-git root passes with `Gated-hash` present, no `Planned-at`, and
      `note:` on stderr; `--base other` on a root whose `other` branch does
      not exist omits `Planned-at`; a rejecting run on a stamped plan keeps
      both stamp lines byte-for-byte. Run the suite and observe the failures.
- [x] 3.2 [req: context-gate-verb] In
      `plugins/s/skills/build/scripts/spec_gate.py`: add `--base` (default
      `main`) to the parser and thread it to `run_gate`; add
      `_resolve_planned_at(plan_path, base)` running `git -C <plan dir>
      merge-base HEAD <base>` via `subprocess.run` (stdlib), returning the
      stripped 40-hex sha or `None` on `OSError` or non-zero exit; in the pass
      branch, after `_strip_gate_section`, call
      `sc.write_plan_stamp(text, sha, sc.plan_gated_hash(text))` before
      writing the file, print `note: Planned-at omitted (<reason>)` to stderr
      when `sha` is `None`, keep `ss.write_status` and `store_autocommit`
      unchanged, and print `stamp: Planned-at <sha|none> Gated-hash <hash>`
      after the `PASS:` line. Update the module docstring. Re-run until 3.1
      and the existing 25 gate tests pass.

## 4. Read-only --check

- [x] 4.1 [req: gate-check-mode] In `test_spec_gate.py`, add a `CheckModeTest`
      class: `--check` on a clean draft exits 0, prints `PASS (check)`, and
      leaves `plan.md` byte-identical; `--check` on a draft whose tasks carry one
      of the gate's placeholder markers exits 2 naming it with `REJECTED
      (check)`, and the
      plan is byte-identical (no section, still `draft`); gate a clean plan
      in a git root, edit `## Implementation`, then `--check` exits 2 with a
      `gated-hash mismatch` finding naming both hashes and the plan is
      unchanged; `--check` on an unstamped clean `ready` plan exits 0;
      `--check no-such-change` exits 1; `--check` on a passing run leaves the
      `AM_FLOW_LOG_DIR` directory empty. Run and observe the failures.
- [x] 4.2 [req: gate-check-mode] In `spec_gate.py`: add `--check`
      (`store_true`); add `_check_gated_hash(root, change)` returning the
      mismatch finding list from `sc.read_plan_stamp` and
      `sc.plan_gated_hash(_strip_gate_section(text))`; add `run_check(root,
      change)` that validates the change directory and plan as `run_gate`
      does, builds `collect_findings(root, change) +
      _check_gated_hash(root, change)`, prints `PASS (check): change '<c>'
      has sufficient context; nothing written.` on exit 0 or `REJECTED
      (check): change '<c>' lacks sufficient context (n finding(s)):` plus
      dot-points on exit 2, and never writes; dispatch from `main` after
      `check_schema_compat`. Re-run until 4.1 passes.

## 5. Show, README, and full verification

- [x] 5.1 [req: plan-header-metadata-lines] In
      `plugins/s/skills/build/tests/test_spec_status.py` next to
      `test_show_status_and_progress` (line 253), add a test that `show` on a
      plan carrying `Epic: e`, a 40-hex `Planned-at`, and a 12-hex
      `Gated-hash` prints both stamp lines; run it — it passes through
      `METADATA_KEYS` without a code change, which is the point.
- [x] 5.2 [req: plan-header-metadata-lines] In `.shipd/README.md` "Header
      metadata" (line 208): replace "Exactly four keys" with the seven keys,
      state that keys may contain hyphens, add dot-points for `Planned-at`
      (merge-base commit id the gate stamped) and `Gated-hash` (gate-approved
      content hash) noting both are gate-written, hex-valued, and preserved by
      every status write, and mention `spec_gate.py --check`.
- [x] 5.3 [req: gate-check-mode] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and `python3 -m unittest discover -s
      evals/tests`; then from the worktree run `python3
      plugins/s/skills/build/scripts/spec_gate.py gate-plan-stamp --check`
      and confirm it reports this change's own status without changing it.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 128 | 1.8k |
| (no tool) | 0 | 1.1k |
| ToolSearch | 4 | 905 |
| SubagentHandback | 3 | 78 |
| TaskStop | 1 | 57 |
| Agent | 4 | 27 |
| Monitor | 1 | 16 |
| **Total** | 141 | 4.0k |
