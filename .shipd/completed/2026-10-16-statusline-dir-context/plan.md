# statusline-dir-context
Status: verified

## Idea

### Motivation

The shipd statusline shows the live spec but not where the session runs or
how much context it has consumed. The user wants both at the end of the line:
the session directory relative to `~` (for example
`~/projects/workspaces/understand`) and the context usage as a four-cell bar
with a percentage (`░░░░ 0%`, `█░░░ 25%`, `████ 100%`).

### Details

Two uncolored segments trail every line the script prints, joined by ` · `:
`☕ <spec line> · ~/<path> · <bar> <pct>%`. The directory comes from
`workspace.current_dir`; the percentage comes from
`context_window.used_percentage`, and its segment drops out when that value
is absent.

### Non-goals

- No change to the silent behavior in a workspace without `.shipd/`.
- No configuration toggle for the new segments.
- No change to the spec pick, the epic marker, or the live-run dot.

Affected capability: `statusline` (modified `statusline-rendering`). Impact:
`plugins/s/integrations/statusline.sh`,
`plugins/s/skills/build/tests/test_statusline.py`, and the plugin version.

## Implementation

- **One suffix, three print sites.** Compute a `suffix` string once after the
  `.shipd/` check and append it to every `printf` that emits a line: the
  `no active specs` line, the `none selected` line, and the rendered spec line.
- **Directory.** Render `$workspace` (already resolved from
  `workspace.current_dir` with the `$PWD` fallback). Replace `$HOME` exactly
  with `~`, and a `$HOME/` prefix with `~/`, using bash parameter expansion
  (`${workspace#"$HOME"/}`) — no external process. Skip the substitution when
  `$HOME` is empty.
- **Context.** Extract `used_percentage` from the stdin JSON with the existing
  `sed` idiom: `"used_percentage"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\)`,
  which captures the integer part and ignores `null`. Clamp to 100. Compute
  filled cells as `(pct * 4 + 50) / 100` in shell arithmetic. Build the bar
  by looping four times, emitting `█` (`\xe2\x96\x88`) or `░`
  (`\xe2\x96\x91`) as raw UTF-8 bytes — bash 3.2 has no `$'\u'`.
- **Format.** Segments are uncolored and join with the existing ` · `
  separator: `<line> · <dir> · <bar> <pct>%`, omitting ` · <bar> <pct>%`
  when no percentage is parsed.
- **Tests.** The test driver gains optional `home` and `context` parameters:
  `home` sets `HOME` in the child environment, and `context` adds
  `{"context_window": {"used_percentage": <v>}}` to the payload. Existing
  substring assertions stay valid.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` from `0.6.303` to
  `0.6.304`.
