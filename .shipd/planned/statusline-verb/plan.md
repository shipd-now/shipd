# statusline-verb
Status: ready

## Idea

Give the `shipd` binary a `statusline` verb that registers the ☕ statusline
in the user's Claude Code settings, and teach `shipd doctor` to surface an
unregistered statusline.

### Motivation

Registering the statusline today means hand-editing `~/.claude/settings.json`
with a snapshot-resolving shell one-liner, and nothing in the toolchain even
reports that it is missing. The user asked for the binary to do it for them,
with `shipd doctor` surfacing the gap.

### Details

- New `statusline` verb on `plugins/s/bin/shipd`: bare invocation is a
  read-only report (registered or not, plus the command this install would
  register); `statusline install [--force] [--settings PATH]` writes the
  `statusLine` entry into the settings file (default
  `~/.claude/settings.json`).
- New `statusline` doctor check: `warn` when the settings file carries no
  `statusLine` key, hinting `shipd statusline install`; never a failure.
- `/s:doctor` remedy table gains the matching consent-gated remedy row.
- `README.md` Statusline section and `docs/getting-started.md` lead with the
  one-command path, keeping the manual snippet as the fallback.

Affected capabilities: `shipd-cli` (modified — `cli-dispatch`, `doctor-verb`;
added — `statusline-verb`), `shipd-doctor` (modified —
`doctor-remedy-boundaries`). Impact: `plugins/s/bin/shipd`,
`plugins/s/skills/build/tests/test_shipd_cli.py`,
`plugins/s/skills/doctor/SKILL.md`, `README.md`, `docs/getting-started.md`,
and the version bump in `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No installer change — `install.sh` keeps writing only the launcher;
  registration stays an explicit post-install step (one command now).
- No project-scope (`.claude/settings.json` in a repo) registration — user
  scope only, matching where the plugin itself is installed.
- No change to `integrations/statusline.sh` or its rendering contract.
- No interactive prompt inside the verb — `install` is explicit intent, and
  `/s:doctor` supplies its own consent layer.

## Implementation

- **The verb lives in-binary** (like `list` and `doctor`), not as an engine
  delegate: it reads/writes the user's settings file, which no engine script
  touches, and must work identically from a checkout and a cache snapshot.
  This is the binary's first mutating verb — a deliberate exception to its
  read-only docstring, explicitly requested; the docstring is updated to name
  the exception.
- **Registered command by mode**, derived from the binary's resolved plugin
  root (the `check_snapshot` dev/cache detection is reused): a repo checkout
  registers `bash <absolute-plugin-root>/integrations/statusline.sh`; a cache
  snapshot registers a shell command that globs the snapshot's parent
  directory, sorts version directories with `sort -V`, and runs the newest
  snapshot's `integrations/statusline.sh` — so the registration survives
  `claude plugin update` without editing. Rejected: registering the versioned
  snapshot path (breaks on update) and routing renders through the `shipd`
  launcher (spawns Python per render; the statusline stays shell-only per the
  constitution's spirit).
- **Settings-edit semantics:** parse the existing JSON, set only the
  `statusLine` key to `{"type": "command", "command": <cmd>}`, and rewrite
  preserving every other key (creating the file and parent directory when
  absent). A different existing `statusLine` refuses with exit 1 naming the
  current command unless `--force` (mirrors `spec_emit --replace`); an
  identical one succeeds idempotently. A file that does not parse as JSON is
  reported as an error and never overwritten. `--settings PATH` overrides the
  target for tests and non-default setups.
- **Doctor check placement:** `check_statusline(settings_path)` appended to
  `default_checks` as a warning-level check with an injectable path, matching
  the in-process injection style `test_shipd_cli.py` uses for the other
  ambient checks. `ok` detail names the registered command's source; `warn`
  detail names `shipd statusline install` so `/s:doctor` can propose it
  verbatim.
- Risk: clobbering a user's settings on a write error; guard: write the new
  JSON to a temp file in the same directory and rename over the original, and
  the malformed-file refusal above.
