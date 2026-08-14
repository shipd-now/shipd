## 1. Epic marker

- [x] 1.1 [req: statusline-rendering] In
      `plugins/s/skills/build/tests/test_statusline.py`, add tests: a
      picked change whose `plan.md` header carries `Epic: some-epic`
      renders `(EPIC)` after the change name; a change without the header
      renders no `(EPIC)`; with two live changes the marker precedes the
      `(1 of 2)` bracket. Run the file and observe the new tests fail.
- [x] 1.2 [req: statusline-rendering] In
      `plugins/s/integrations/statusline.sh`, extract the `^Epic:` slug
      from each candidate's `plan.md` (sed, same idiom as `status_of`)
      into a new `cand_epic` parallel array in `add_candidate`, and in the
      render section append ` (EPIC)` to `name_seg` (before the
      `(1 of X)` suffix) when the picked candidate's epic value is
      non-empty. Confirm the 1.1 tests pass.

## 2. Breathing run dot

- [x] 2.1 [req: statusline-rendering] In
      `plugins/s/skills/build/tests/test_statusline.py`, add tests
      fabricating `.shipd/autopilot/e-heartbeat.json` in the temp workspace:
      an `active` change plus a fresh heartbeat containing
      `"state": "running"` renders the U+25CF dot before `active` (assert
      on the ANSI-stripped line); a `"run_state": "running"` variant also
      renders the dot; a `"state": "finished"` heartbeat renders no dot; a
      `running` heartbeat aged past 3600 s via `os.utime` renders no dot;
      a `ready` picked change with a fresh `running` heartbeat renders no
      dot. Run the file and observe the new tests fail.
- [x] 2.2 [req: statusline-rendering] In
      `plugins/s/integrations/statusline.sh`, add a `run_is_live` helper
      that globs `"$workspace"/.shipd/autopilot/`*`-heartbeat.json` and
      returns success when any file has `mtime_of` within 3600 s of
      `date +%s` and matches
      `"(run_)?state"[[:space:]]*:[[:space:]]*"running"` (grep -E); in the
      render section, when the picked status is `active` and
      `run_is_live` succeeds, prefix the status segment with the U+25CF
      dot (raw UTF-8 `printf '\xe2\x97\x8f'`) colored
      `\033[38;5;<n>m` where `<n>` is picked from the ramp
      `46 40 34 28 22 28 34 40` by `$(date +%s) % 8`, followed by a space
      and the existing colored status. Confirm the 2.1 tests pass.

## 3. Ship gate

- [x] 3.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next free patch above
      `origin/main`'s current value (0.6.5 as of planning; take the next
      free patch if another merged change claimed it).
- [x] 3.2 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` from
      the repo root and observe zero failures; then pipe a session JSON at
      a fixture workspace (active change + fresh fabricated `running`
      heartbeat) through `plugins/s/integrations/statusline.sh` and
      observe the `(EPIC)` marker and green dot in the raw output. If the
      `delivery-dashboard` change has merged, read its heartbeat-writing
      code in `plugins/s/skills/build/scripts/autopilot.py` and confirm
      it writes a state value `running` matched by the 2.2 regex; if the
      merged key/value pair differs, update the regex and the 2.1
      fixtures to match it.
