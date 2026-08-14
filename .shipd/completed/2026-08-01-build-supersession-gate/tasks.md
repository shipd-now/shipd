## 1. check-base verb

- [x] 1.1 [req: check-base-verb] Add failing tests to
      `plugins/s/skills/build/tests/test_spec_status.py` for `check-base`:
      a clean change (matching `base:` hashes, new ADDED ids) exits 0 with a
      clean summary and no finding lines; a MODIFIED entry with a wrong
      `base:` prints a `stale-base` line with expected/actual hashes and
      exits 4; an ADDED entry whose id exists in the master prints
      `id-collision` and exits 4; a MODIFIED entry with an unknown id prints
      `missing-master` and exits 4; the verb modifies no file. Run the suite
      and observe the new tests fail (verb absent).
- [x] 1.2 [req: check-base-verb] Implement `check-base [change]` in
      `plugins/s/skills/build/scripts/spec_status.py`: resolve the change
      via the existing `_resolve_change` default-to-selected path; `import
      spec_merge` (same `sys.path` mechanism as the `spec_common` import) and
      reuse `spec_merge.master_path` for master resolution and
      `sc.content_hash` for comparison; parse deltas with `sc.parse_delta`
      and masters with `sc.parse_spec`; print one
      `<capability>/<id>: <kind>` line per finding (hash detail on
      `stale-base`) plus a summary line; exit 0 clean, 4 on findings. Confirm
      the 1.1 tests pass.

## 2. Build skill gate

- [x] 2.1 [req: supersession-gate] In `plugins/s/skills/build/SKILL.md`
      Phase 0 step 1 (already-planned short-circuit), add the supersession
      gate prose: after adopting a linted change, run `check-base` (path via
      `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`); clean →
      proceed; findings → read the affected masters and recent base-branch
      history, classify drift (proceed, carry findings into plan review) vs
      superseded (stop, report, ask the user to abandon or re-scope; never
      spawn sub-agents on a superseded plan).

## 3. Ship gate

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.6.14 → 0.6.15, then run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm the full suite is green.
