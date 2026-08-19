# aider-adapter
Status: verified

## Idea

Give aider a real generated surface: `shipd harness add aider` writes one
ownership-marked `shipd-conventions.md` — a conventions file distilled from
the body source's command index — instead of skipping the harness.

### Motivation

Aider is the one registry harness shipd generates nothing for: its
conventions-file dialect has no renderer and both surfaces are `None`, so
`add aider` reports `skipped (no repo surface)` and aider users drive shipd
entirely by hand. The user asked for the conventions-file adapter the epic
sketched but left unbuilt.

### Details

- Registry: aider's `repo_pattern` becomes the literal single file
  `shipd-conventions.md` (dialect stays `conventions-file`; `user_dir` stays
  `None`, features stay empty).
- Generation: a real `conventions-file` renderer in `harness_generate.py`,
  fed by a new authored partial `plugins/s/harness/bodies/_conventions.md`.
- One README sentence in the harness-mode section; tests; version bump.

Affected capabilities: `harness-registry` (modified) and `harness-verb`
(modified). Impact: `plugins/s/skills/build/scripts/harness_registry.py`
(one entry), `plugins/s/skills/build/scripts/harness_generate.py`,
`plugins/s/harness/bodies/_conventions.md` (new),
`plugins/s/skills/build/tests/test_harness_generate.py`, `README.md`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- Never edit or append to a user's own `CONVENTIONS.md` — the ownership
  marker and foreign-file refusal are file-level, so shipd only writes the
  dedicated file it owns outright.
- No TUI change: `install_tui._label` derives "(repo only)" from the missing
  user-mode surface (install_tui.py:332), which becomes accurate for aider
  the moment the registry entry carries a repo surface.
- No aider feature declarations, no user-global surface, and no change to
  any other harness's rendering.
- No `.aider.conf.yml` writes — wiring `read: shipd-conventions.md` is the
  user's one manual step, stated in the add report and the README.

## Implementation

- **Registry entry:** `repo_pattern: "shipd-conventions.md"` — a literal
  path with no `{command}` placeholder. The `registry-data` invariant is
  re-scoped accordingly: the placeholder is required only for dialects other
  than `conventions-file`, whose pattern is a literal single-file path.
  Rejected: a new `conventions_file` key — `repo_pattern` already is "the
  repo-relative generated-file path", and `has_surface` keys off it, which
  is exactly what makes `add`/`remove`/`status` and the TUI label work
  unchanged.
- **The conventions template** `plugins/s/harness/bodies/_conventions.md`
  (underscore-prefixed, so `harness_bodies.commands()` ignores it, matching
  `_preamble.md`): authored prose — what shipd is and the
  plan → gate → build → review loop; a `{preamble}` placeholder; a
  `{command_index}` placeholder; guidance that aider users run the `shipd`
  CLI and `$S` engine scripts via `/run` and `--read` the planned change's
  `plan.md`/`tasks.md` into the chat; and the closing note to add
  `read: shipd-conventions.md` to `.aider.conf.yml`.
- **Renderer:** `harness_generate.render_file` gains a `conventions-file`
  branch (replacing the current `ValueError`): read `_conventions.md` and
  `_preamble.md` directly from the bodies dir, substitute `{preamble}` with
  the preamble's content and `{command_index}` with one line per
  `harness_bodies.commands()` entry —
  `- shipd-<command> — <harness_bodies.description(command)>` — and emit
  `MARKER` first, exactly like the other dialects. No frontmatter, no
  per-command files, no reference files (aider declares no
  `file-references`). Rejected: reusing `harness_bodies.render` — it is
  command-oriented (gates, refs); the conventions template needs only two
  flat substitutions.
- **Surface semantics:** `add aider --root X` writes exactly
  `X/shipd-conventions.md`; the surface resolver treats a pattern without
  `{command}` as one target file for the whole harness. Ownership marker,
  byte-idempotent re-run, `--force` on an unmarked existing file, `remove`
  deleting only the marked file, and `status`
  (`absent`/`installed`/`stale`/`foreign`) all follow from the existing
  file machinery. `add aider --user` still reports
  `skipped (no user surface)` — observed today: repo mode reports
  `skipped aider (no repo surface)`, exit 0, nothing written; that skip
  path moves to user mode only. The add report for aider appends the
  `.aider.conf.yml` `read:` pointer line.
- **README:** one sentence in the harness-mode section naming aider's
  conventions file and the `read:` wiring step.
- **Version bump:** `plugins/s/.claude-plugin/plugin.json` to the next
  patch above the branch's post-base-merge value.

Risk: a literal `repo_pattern` reaching the per-command path formatter
would produce one file overwritten seventeen times — averted by branching
on the dialect before per-command iteration, with a test pinning exactly
one write for aider.
