# statusline-chain
Status: verified
Planned-at: 15485739ff75f40e0ed1b644e00266a68155b33d
Gated-hash: 194b2e47bbed

## Idea

Let `shipd statusline install` coexist with a statusline the user already
has — shipd's line first, the existing statusline after it — and let the user
choose which shipd segments show, in what order, and on which line.

### Motivation

On a machine that already registers a statusline, `shipd statusline install`
refuses with "already registers a different statusline … pass --force to
replace it". The only way forward discards the user's own statusline. The
doctor also reports any registered command as `ok`, so the install finish's
automatic remedy never adds shipd's line on such a machine.

### Details

`install` wraps a foreign registration as `<shipd cmd> --then '<existing>'`
and prints `added statusline above existing statusline`. The statusline
script runs the `--then` command after its own output, with the same session
JSON on stdin, so the user sees shipd's line on top and theirs beneath it.
An existing shipd registration — any checkout or snapshot path — is updated
in place and keeps its `--then` tail. `--force` still replaces outright.

The shipd output is built from three segments — `spec`, `directory`,
`context` — arranged by a layout saved in the global `~/.shipd-config.json`
(`{"statusline": {"lines": [["spec", "context"]]}}` by default, so the
directory is off and the context bar on). `shipd statusline layout
spec,context directory` puts the directory on a second line; `shipd
statusline layout context,spec` puts the context bar beside the coffee cup;
`shipd statusline install --show directory` / `--hide context` adjust it.
The install verb renders the saved layout into the registered command as
`--line` arguments, so the script still reads no configuration file.

### Non-goals

- No change to the vendored per-repo statusline (`shipd vendor`).
- No uninstall or unchain verb.
- No new segment types beyond `spec`, `directory`, and `context`.

## Implementation

- **Script.** In `plugins/s/integrations/statusline.sh`, before reading
  stdin: `chain=""; if [ "$1" = "--then" ]; then chain="$2"; fi`. After
  `input=$(cat)`, define `run_chain()` that, when `$chain` is non-empty, runs
  `printf '%s' "$input" | bash -c "$chain"`, and install it with
  `trap run_chain EXIT` so every `exit` path runs it after shipd's output.
  Verified on macOS bash 3.2.57: the trap runs after `exit 0`, and the
  chained command receives the full JSON.
- **Recognition.** Add `SHIPD_STATUSLINE_MARK = "integrations/statusline.sh"`
  and `_is_shipd_statusline(command)` (substring test) to `plugins/s/bin/shipd`.
- **Chain extraction.** `_chained_command(command)` returns the token after
  `--then` from `shlex.split(command)`, or `None` when there is no `--then`
  or `shlex.split` raises `ValueError`.
- **Install.** In `cmd_statusline` replace the refusal with: no entry →
  `command`; `--force` → `command`; shipd's entry → `command` plus
  ` --then <shlex.quote(chained)>` when `_chained_command` finds one; a
  foreign entry → `command + " --then " + shlex.quote(current)`. Write only
  when the result differs from `current`. For the foreign case print
  `added statusline above existing statusline` and `  existing: <current>`;
  otherwise keep today's `statusline registered in <path>` lines.
- **Bare report.** When the current entry is foreign, print
  `  this install would add the shipd statusline above it` instead of the
  plain `would register` line.
- **Doctor.** `check_statusline` warns when the command is not shipd's:
  `registers a different statusline (<command>) in <path> — run
  \`shipd statusline install\` to add shipd's above it`.
- **Layout arguments.** In `statusline.sh`, replace the single `--then`
  check with a bash 3.2 loop over all arguments: `--line <segs>` appends to
  an indexed array `lines`, `--then <cmd>` sets `chain`, anything else is
  shifted past. No `--line` → `lines=("spec,context")`.
- **Layout rendering.** Compute `spec_seg` (today's text after `☕ `, with
  the trailing directory/context suffix removed), `dir_seg`, and `ctx_seg`
  (empty when no percentage) once. Replace the three print sites with: set
  `spec_seg`, call `render_lines`, `exit 0`. `render_lines` walks `lines`;
  per line it splits on `,`, maps each name to its segment, skips empty and
  unknown ones, joins with ` · `, skips an empty line, and prints the first
  printed line with the `☕ ` prefix.
- **Layout config.** In `plugins/s/bin/shipd`, add
  `STATUSLINE_SEGMENTS = ("spec", "directory", "context")`,
  `DEFAULT_STATUSLINE_LINES = [["spec", "context"]]`,
  `_load_statusline_layout(path)` (reads `~/.shipd-config.json`; absent file
  or key → default; malformed → error naming `statusline`),
  `_validate_layout(lines)`, and `_save_statusline_layout(path, lines)`
  using `_write_settings` (atomic, preserves other keys). The config path is
  `Path.home() / ".shipd-config.json"`, overridable with `--config` on both
  verbs for tests.
- **Command composition.** `statusline_command(plugin_root, lines=None)`
  appends ` --line <a,b>` per layout line to the base command; the install
  branches from the chain work append ` --then …` after it.
- **Verbs.** `install` gains repeatable `--show SEG` / `--hide SEG`; it
  loads the layout, applies them, validates, saves (only when changed), then
  registers. New `statusline layout [LINE ...]`: bare prints each line as
  `line <n>: <seg> · <seg>`; with arguments it validates, saves, and, when
  the registered command is shipd's, re-registers through the same install
  path (keeping `--then`). Unknown segment, duplicate, or empty → exit 2.
- **Docs.** `docs/cheatsheet.md` row for `statusline` reads
  `statusline [install|layout] [--show SEG] [--hide SEG] [--force]` /
  `Register the shipd statusline above any existing one, and choose its
  segments and lines.`
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` one patch above
  the version `main` carries when the build starts.

## Readiness attestation

### Problem and motivation

`install` refuses on a foreign statusline, and the doctor never flags one.

Evidence:

- The user's run: `shipd statusline install` → `Error: … already registers
  a different statusline: …/node …/claude-statusline.mjs — pass --force to
  replace it`.
- `plugins/s/bin/shipd` `cmd_statusline` exits `1` when `current != command`
  without `--force`; `check_statusline` returns `ok` for any command.

### Scope and non-goals

The chain flag, install logic, and doctor check; the vendor flow stays out.

Evidence:

- In scope: `statusline.sh` argument handling, `cmd_statusline`,
  `check_statusline`, the cheatsheet row.
- Out of scope: `vendor_statusline_command` and the vendor add/remove paths.

### Affected capabilities and files

Two capabilities, three modified requirements and one added.

Evidence:

- `statusline`: added `statusline-chain`; modified `statusline-integration`
  (base 8505a02a82e4).
- `statusline`: modified `statusline-rendering` (base 713b70eea5f2).
- `shipd-cli`: `statusline-verb` (base ce4f05209abe), `doctor-verb`
  (base 7b776fa09544); added `statusline-layout`.
- Tests: `plugins/s/skills/build/tests/test_statusline.py`,
  `test_shipd_cli.py` (`StatuslineVerbTest`, the doctor statusline tests).
- Runnable premise: a bash 3.2 script with `trap run_chain EXIT` printed its
  own line, then the chained `python3` command printed the stdin JSON.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Ours first, existing after, and the exact message: stated by the user.
- `--force` keeps its replace meaning; shipd recognition by
  `integrations/statusline.sh`: settled by the existing verb's contract.
- Layout saved in the global `~/.shipd-config.json`, set through the
  install verb, and folded into this change: settled by the user (Q1, Q2).
- Directory off and context on by default, multi-line and ordered layout:
  stated by the user.

## Questions and answers

### Q1: Where do the statusline segment settings live?
- **Question:** Where should the statusline's per-segment toggles live?
  Options: (a) flags on the registered command, set via `shipd statusline
  install --show/--hide`; (b) a `statusline` key in `~/.shipd-config.json`
  read by the script on every render. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Options on `shipd statusline install`, with the layout saved in
  the global shipd config (`~/.shipd-config.json`) so every later install
  reuses it and shipd can be told to change it, e.g. to add the directory.
- **Queued:** q-statusline-segment-toggle-storage

### Q2: Fold segment configuration into this change or sequence it?
- **Question:** Should configurable segments join `statusline-chain` or ship
  as a separate change after it merges? Options: (a) fold in; (b) separate.
  Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Fold it into this change.
- **Queued:** q-statusline-segments-fold-or-sequence
