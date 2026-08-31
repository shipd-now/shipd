# pi-harness-esc-quit
Status: verified

## Idea

Add the Pi coding agent as the fourteenth registry harness, and make `Esc`
abort the `shipd install` multi-select the way `q` already does.

### Motivation

The registry carries `oh-my-pi` but not `pi` — a different agent from a
different vendor — so Pi users cannot install the shipd commands at all, and
the install multi-select drops a bare `Esc` as a no-op even though `Esc` is
the reflex for leaving a picker.

### Details

- Append a `pi` entry to `HARNESSES` in
  `plugins/s/skills/build/scripts/harness_registry.py`: `repo_pattern`
  `.pi/prompts/shipd-{command}.md`, `user_dir` `~/.pi/agent/prompts/`,
  dialect `yaml`, frontmatter `("description", "argument-hint")`, features
  `("file-references",)`.
- Update the `harness-registry` spec's thirteen-entry counts and id
  enumeration to fourteen, and pin Pi's researched paths in a scenario.
- Update `README.md`'s "registry's thirteen harnesses" wording and the
  `project-readme` spec to fourteen.
- Map a lone `Esc` byte to `ABORT` in `install_tui.py`'s `_KEYS`, and name
  `esc` in the picker's `HINT` line.
- Bump the plugin version.

Affected capabilities: `harness-registry` (modified), `project-readme`
(modified), `install-tui` (modified). Impact:
`plugins/s/skills/build/scripts/harness_registry.py`,
`plugins/s/skills/build/scripts/install_tui.py`,
`plugins/s/skills/build/tests/test_harness_registry.py`,
`plugins/s/skills/build/tests/test_install_tui.py`, `README.md`,
`plugins/s/.claude-plugin/plugin.json`; no new dependencies.

### Non-goals

- No new dialect and no new feature-vocabulary entry — Pi reuses the existing
  `yaml` dialect and the declared feature set.
- No changes to `harness_generate.py` or `harness_bodies.py`; the registry is
  data the existing generation path already reads.
- No Pi extension, skill, or `settings.json` surface — prompt-template command
  files only, matching every other harness.
- No `Esc` handling in the line-prompt fallback — `Esc` is a raw-mode
  keypress, not a typed line.
- No change to how unrecognized escape sequences decode.

## Implementation

- **Pi is a separate harness from oh-my-pi.** `oh-my-pi` (`omp`, can1357) and
  `pi` (earendil-works) are different agents with different command surfaces;
  the registry gets a second entry rather than a widened one. Rejected:
  treating `.pi/` as an alternate path on the `oh-my-pi` entry — the entries
  declare one surface each, and the two agents' paths do not overlap.
- **Data-only addition.** The module docstring states a vendor path move is
  "a one-entry edit"; generation reads paths, dialect, and features from the
  entry alone. Rejected: any Pi-specific generation branch — the `yaml`
  dialect already renders it.
- **Paths from the vendor docs**, verified 2026-08-31 against Pi's
  prompt-templates documentation: global templates are discovered from
  `~/.pi/agent/prompts/*.md` and project templates from `.pi/prompts/*.md`,
  and the filename becomes the command name (`review.md` → `/review`). Hence
  `repo_pattern` `.pi/prompts/shipd-{command}.md` and `user_dir`
  `~/.pi/agent/prompts/`, which keeps the `shipd-` command-id prefix.
- **Frontmatter is `("description", "argument-hint")`.** Both are documented
  Pi template fields, and `FIXED_FRONTMATTER` in `harness_generate.py` carries
  a value for `argument-hint` (`[input]`), so both render — the same shape the
  `codex` entry already uses. Rejected: `description` alone — it would drop a
  field Pi displays in autocomplete.
- **Features are `file-references` only.** Pi's docs state it "intentionally
  does not include built-in MCP, sub-agents, permission popups, plan mode" or
  background bash, while `@` fuzzy file references are a documented feature.
  So `subagents`, `question-dialogs`, and `background-tasks` stay undeclared
  and their body gates render their else branches.
- **Entry appended after `opencode`.** The registry is insertion-ordered, not
  alphabetical; `ids()` order and the spec's id enumeration follow the entry
  order.
- **Counts stay spelled out.** The registry and README specs spell
  "thirteen"; the deltas re-spell "fourteen" in the same style rather than
  switching to digits.
- **`Esc` aborts through the existing decoder branch, not a new one.**
  `decode_keys` already tests `byte == ESC and data[index + 1:index + 2] ==
  b"["` first and consumes three bytes for a CSI sequence, so the single-byte
  `_KEYS` lookup only ever sees an `Esc` that introduces no `\x1b[` sequence.
  Mapping `b"\x1b"` to `ABORT` there therefore leaves arrows and unrecognized
  CSI sequences exactly as they are. Rejected: a dedicated `ESCAPE` key name
  and a reducer branch — `Esc` and `q` are the same verdict, and a second name
  would duplicate it.
- **The line prompt is untouched.** `line_prompt` reads whole submitted lines,
  where "pressing Esc" has no meaning; adding `"\x1b"` to its abort words
  would document an affordance the mode does not have. Rejected: mirroring the
  key there for symmetry.
- **Runnable premises.** `plugins/s/bin/shipd harness` was run before
  planning: it printed the thirteen entry lines and exited 0, so the
  data-driven list/show/add surfaces need no code change for a new entry.
  `decode_keys` was run on the four relevant inputs: `b"\x1b"` → `[]` (the
  behavior this change replaces), `b"\x1b[A"` → `['up']`, `b"\x1b[C"` → `[]`,
  `b"q"` → `['abort']`.

Risk: an `Esc` split across two reads — the byte ending one chunk and `[A`
opening the next — would now abort instead of moving the cursor. The decoder
already assumes a terminal delivers a burst whole (its own docstring), so the
assumption is pre-existing rather than introduced, and raw-mode blocking reads
deliver a CSI sequence in one chunk.

Risk: Pi has renamed its repository (`badlogic/pi-mono` → `earendil-works/pi`)
and could move its template directories; the researched-paths scenario pins
the currently documented paths so a future vendor move is a deliberate
one-entry edit with a spec update, not silent drift.
