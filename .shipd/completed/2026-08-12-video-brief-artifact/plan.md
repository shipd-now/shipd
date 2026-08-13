# video-brief-artifact
Status: verified
Epic: video-ingest
Theme: developer-experience

## Idea

Give the video intent brief a first-class artifact kind: an emit verb that
installs it, a lint mode that validates it, and a read verb that prints it.

### Motivation

The `video-ingest` epic's remaining members all produce or consume a brief that
has nowhere to land — the engine has no verb that installs one and no checks
that would stop an ungrounded brief from entering the tree.

### Details

- Add `spec_emit.py video <slug> --from <file>` installing a brief at the
  resolved `<content-dir>/video/<slug>/brief.md` under the existing
  validate-then-install rule.
- Add in-process `lint_video(root, slug, errors)` enforcing the brief grammar,
  called only by the emit engine — library lint never walks `video/`.
- Add `spec_status.py cat video <slug>`.
- Document the brief grammar and the reserved `video/` folder in
  `.shipd/README.md`.

Affected capabilities: `spec-io` (modified), `shipd-spec-lint` (added),
`shipd-spec-format` (added). Impact:
`plugins/s/skills/build/scripts/spec_emit.py`, `spec_lint.py`,
`spec_status.py`; tests under `plugins/s/skills/build/tests/`;
`.shipd/README.md`; the plugin version in
`plugins/s/.claude-plugin/plugin.json`. No new dependencies — stdlib only.

### Non-goals

- No ingest pipeline, no ffmpeg, no ASR or diarization — this member is the
  artifact contract only.
- No `/s:video-ingest` skill; nothing authors a brief yet.
- No `spec_lint.py` CLI flag for briefs — validation runs only at install, the
  same way research reports work.
- No validation that a brief's referenced frames exist.
- No `/s:epic` linking support for briefs (its own member).

## Implementation

**The `research` artifact is the template, deliberately.** `emit_video` mirrors
`emit_research` (`spec_emit.py:179`) — same `_install_dir` wrapper, same
remove-on-failure semantics, same `--replace` rule — and `lint_video` mirrors
`lint_research` (`spec_lint.py:793`). Rejected: a bespoke installer for briefs;
the engine's value is that every artifact kind lands the same way.

**Reuse the existing citation machinery rather than re-implementing it.**
`_citation_markers_outside_code`, `_section_lines`, and `SOURCE_ENTRY_RE`
already exist in `spec_lint.py` and already handle the fenced-code-block edge
case. `lint_video` calls them.

**No CLI lint flag, and library lint never walks `video/`.** Research set this
precedent (`--epic` exists, research has no flag) so `ci`'s library-lint step
keeps ignoring the folder. Rejected: a `--video` flag — it would invite the
library lint to walk a folder whose contents are only ever installed through the
engine.

**Two rules make the brief worth having, and both are mechanical:**

1. *Every level-3 intent carries at least one `[n]` marker.* This enforces the
   epic's D9 — an unciteable claim belongs in gaps-and-caveats, never in the
   intents — so an ungrounded intent cannot be installed.
2. *Every source entry opens with a bracketed timestamp and a speaker.* A source
   here is an utterance, not a URL; without this the artifact degrades into a
   free-text summary.

Timestamps (`[00:14:22.4]`) contain colons and therefore never match the
citation-marker pattern, so the two rules do not interfere.

**Frame references are not existence-checked.** They point into the bundle at
`~/.shipd/video/<slug>/`, deliberately outside the repo (epic D8), which may be
pruned at any time; validating them would couple a repo artifact to a scratch
directory's lifetime.

**Header grammar.** `Video:` is required — provenance is the point of the
artifact — while `Bundle:` and `Decider:` are optional. The brief uses its own
small header parse rather than `parse_plan_metadata`, which is the plan/epic
metadata vocabulary and would reject these keys.

Risk: the grammar is fixed before any skill authors a brief, so a later member
may want a section this change does not permit. Guarded by validating only the
required skeleton — unknown level-2 sections are not an error, so the format can
grow without a breaking change.

**Plugin version bump.** This change touches `plugins/s/`, so
`plugins/s/.claude-plugin/plugin.json` must go `0.6.75` → `0.6.76` in the same
PR or the cached snapshot never picks it up (`AGENTS.md`).
