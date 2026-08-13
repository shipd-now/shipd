# statusline-epic-pulse
Status: verified

## Idea

Show an `(EPIC)` marker after the statusline name when the picked change
belongs to an epic, and a breathing green dot beside `active` while an
autopilot run's heartbeat is live.

### Motivation

The statusline gives no hint that the displayed change is an epic member, and
a live autopilot run is indistinguishable from an idle repo — the user cannot
tell that background delivery work is happening. Both facts are already on
disk (the plan's `Epic:` header and the autopilot heartbeat file) but are not
surfaced.

### Details

- Render the literal marker `(EPIC)` after the name segment (before any
  `(1 of X)` position bracket) when the picked change's `plan.md` header
  carries an `Epic:` line.
- Prefix the status segment with a solid dot (U+25CF) when the picked change
  is `active` and a fresh heartbeat under `.shipd/autopilot/*-heartbeat.json`
  records run state `running`; the dot breathes through an 8-step
  light→dark→light ramp of xterm-256 greens, one step per second.
- Treat a heartbeat older than 3600 seconds as dead (crashed run): no dot.

Affected capabilities: `statusline` (modified). Impact:
`plugins/s/integrations/statusline.sh`,
`plugins/s/skills/build/tests/test_statusline.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump). The heartbeat
contract comes from the in-flight `delivery-dashboard` change's
`autopilot-heartbeat` delta; the statusline only reads the file, so there is
no code dependency — the dot stays dormant until heartbeats exist.

### Non-goals

- No epic slug in the line — the literal `(EPIC)` marker only.
- No dot on non-`active` statuses, and no run detail (member/stage) in the
  line — the delivery dashboard owns run observability.
- No sub-second animation — the script is stateless and macOS bash 3.2 has
  no sub-second clock, so the fade steps once per second.
- No `.shipd-config.json` resolution — the literal `.am` paths remain (the
  documented statusline limitation).

## Implementation

- **Epic detection** — in `add_candidate`, sed `plan.md` for
  `^Epic:[[:space:]]*<slug>` into a new `cand_epic` parallel array (the
  script's existing bash-3.2 idiom); render ` (EPIC)` inside the name
  segment before the position bracket. Rejected: reading `.shipd/epics/` —
  membership is already declared in the plan header the script parses.
- **Liveness probe** — a `run_is_live` helper globs
  `"$workspace"/.shipd/autopilot/`*`-heartbeat.json`; a file is live when
  `mtime_of` is within 3600 seconds of `date +%s` (2× the default 1800 s
  session budget, so a long silent stage attempt keeps the dot while a
  crashed run's stale file loses it) and it matches
  `"(run_)?state"[[:space:]]*:[[:space:]]*"running"` — the heartbeat delta
  pins the value vocabulary (`running`/`finished`) but not the key name, so
  the probe tolerates both plausible keys. Rejected: `pgrep -f
  autopilot.py` — sees only local processes and adds process sniffing to
  every render.
- **Breathing dot** — glyph U+25CF emitted as raw UTF-8
  (`printf '\xe2\x97\x8f'`; `$'\uXXXX'` is bash 4.2+), colored with
  `\033[38;5;<n>m` from the 8-entry ping-pong ramp `46 40 34 28 22 28 34 40`
  indexed by `$(date +%s) % 8`: light→dark→light, one step per second, full
  cycle every 8 s. The statusline re-renders on Claude Code's refresh
  cadence, so no state is kept between invocations. Rejected: truecolor
  escapes — 256-color has wider terminal support.
- **Render order** — `<name> (EPIC) (1 of X) · <dot> <status> · <tasks>`;
  the dot lives inside the status segment so the ` · ` separators stay
  uncolored, and the dot's color is independent of the status color (which
  stays yellow for `active`).
- **Constitution compliance** — bash 3.2 only, no Python/Node spawned from
  the script; tests extend the existing black-box harness in
  `test_statusline.py`, fabricating heartbeat fixture files and aging them
  with `os.utime` (no autopilot involvement).
- **Version bump** — `plugins/s/.claude-plugin/plugin.json` to the next
  free patch above `origin/main`'s value at build time (0.6.4 → 0.6.5 as of
  planning; take the next free patch if `delivery-dashboard` claims it
  first). Statusline edits run live from the repo, but the
  touching-`plugins/s/` bump rule applies regardless.

Risk: heartbeat schema drift when `delivery-dashboard` merges — guarded by
the key-tolerant regex and a build-time verification task that checks the
merged schema still writes a `running` state value the probe matches.
