# video-brief-grammar-revision
Status: verified
Epic: video-drop-diarization

## Idea

Remove the speaker surface from the video brief grammar, the linter, and the
ingest skill, replace decider arbitration with recency, and add the `Project:`
header field with a target-mismatch guard on `/s:plan`.

### Motivation

The engine member removed every speaker from the bundle, but the grammar still
requires a `## Speakers` section holding at least one `- <name> — <label>` entry
— so `/s:video-ingest` cannot currently install a lint-clean brief at all. The
skill also still directs a naming round through `samples`, `merge-speakers`, and
`roster`, three verbs that no longer exist.

### Details

- Drop the `## Speakers` requirement and the speaker name from `## Sources`
  entries; a source entry is its `[HH:MM:SS]` anchor and what was said.
- Retire the speaker-naming and decider-arbitration requirement, replacing its
  conflict half with a recency rule: the latest statement about a target wins,
  and an unresolved contradiction goes to `## Open questions`.
- Add an optional `Project:` header line validated against the workspace
  registry, and have `/s:plan` refuse a brief whose project differs from the
  planning repository's unless `--cross-project` is given.
- Update the `plan-video-brief` eval fixture to a brief with no speaker surface.

Affected capabilities: `shipd-spec-format`, `shipd-spec-lint`, `shipd-video-ingest`,
`shipd-plan` (all modified). Impact:
`plugins/s/skills/build/scripts/spec_lint.py`,
`plugins/s/skills/build/tests/test_spec_lint.py`,
`plugins/s/skills/video-ingest/SKILL.md`,
`plugins/s/skills/plan/SKILL.md`,
`evals/cases/plan-video-brief/fixture/.shipd/video/report-json-export/brief.md`,
and the plugin version in `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No engine, bundle, or transcript change — the engine member already shipped
  that, and nothing here touches `video_ingest.py`.
- No modification of `video-skill-pipeline`: its staged-pipeline description is
  already speaker-free and needs no edit.
- No retrofit of installed briefs; a surviving `## Speakers` section stays
  lint-clean as an unrecognized level-2 section.

## Implementation

- **`## Speakers` goes; `## Sources` needs no regex change.**
  `VIDEO_TIMESTAMP_RE` (`spec_lint.py:861`) is
  `^\[\d{2}:\d{2}:\d{2}(?:\.\d+)?\]\s+\S` — it has only ever required a
  timestamp followed by some non-space text, never a speaker. Dropping the
  speaker from source entries is therefore a documentation and specification
  change; the only code removal is the `## Speakers` section check and its
  `VIDEO_SPEAKER_ENTRY_RE`.
- **Arbitration is replaced, not merely deleted.** `video-skill-arbitration`
  bundles the naming round with conflict resolution, so removing it wholesale
  would silently drop conflict handling. It is retired and a new
  `video-skill-conflict-recency` requirement takes over the surviving half:
  the latest statement about a target is the recorded intent, the superseded one
  is retained with its timestamp, and an unresolved contradiction goes to
  `## Open questions`. Rejected: modifying the existing requirement in place —
  its id is bound to decider-by-speaker semantics that no longer exist.
- **Recency is sound here because the timestamps are trustworthy.** Word
  timestamps were verified exact against an independently transcribed clip
  during the investigation that motivated this epic, so ordering by time is a
  reliable substitute for ordering by a named decider.
- **`Project:` reuses the initiative brief's mechanism.** `lint_video` calls the
  existing `_check_brief_project` (`spec_lint.py:654`), resolving the workspace
  root with `sc.find_workspace_root(root)` as `lint_initiative`'s caller does.
  The field is optional: a brief without it never loads the registry, so a
  registry-less workspace is unaffected. Rejected: a new `Product:` key, which
  would duplicate that validator for one concept.
- **The plan guard compares only when both sides are known.** `/s:plan` refuses
  a mismatch and stops without emitting, unless the invocation carries
  `--cross-project`; where the brief has no `Project:` or the repository
  resolves to no declared project, no comparison happens. Otherwise a
  registry-less workspace would have every video-entry plan refused.

Risk: two `SKILL.md` files change, and skills are only exercised by real
sessions, so the unit suite cannot prove the guard or the removed naming round
behave. The `plan-video-brief` eval case is the compensating control and is run
as a task.
