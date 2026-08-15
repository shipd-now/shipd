# video-cursor-grounding
Status: verified
Epic: video-ingest

## Idea

Port automikk's `video-cursor-grounding` change — pointer localization by
gated frame differencing, verified carry-forward of a resting pointer, and
per-frame pointer zoom crops the intent-grounding step reads — into shipd's
video-ingest engine, closing the `video-ingest` epic's last unplanned member.

### Motivation

The `video-cursor-grounding` member shipped in automikk (PR #211, `af7ec71`)
after shipd's engine-port snapshot was taken, so shipd's `video_ingest.py`
has no cursor code at all and the epic's last member sits unplanned on the
board. Porting the finished, upstream-verified implementation closes the gap
— and the epic — without re-deriving settled work.

### Details

- Port the cursor pipeline into
  `plugins/s/skills/video-ingest/scripts/video_ingest.py` (+501/−5): pointer
  localization, resting-pointer carry-forward, and zoom-crop emission with
  index entries.
- Port the new unit test file
  `plugins/s/skills/video-ingest/tests/test_video_cursor.py` (521 lines).
- Port the `SKILL.md` additions describing how crops ground an intent's
  target.
- Bump the plugin version.

Affected capabilities: `video-pipeline`, `shipd-video-ingest` (modified —
ADDED requirements). Impact:
`plugins/s/skills/video-ingest/scripts/video_ingest.py`,
`plugins/s/skills/video-ingest/tests/test_video_cursor.py` (new),
`plugins/s/skills/video-ingest/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No changes to the build-engine scripts, the epic skill, or the linter —
  the previous change (`epic-video-brief`) carried those; this one is
  video-ingest only.
- No re-litigation of upstream design decisions — the port carries #211 as
  shipped and reviewed in automikk.
- No porting of automikk's archived artifacts for this member — shipd's own
  pipeline records this change.
- No new pre-existing-residual sweep beyond the two lines the port report
  names in `SKILL.md` — the wider bare-`am:` cleanup across other skills is
  its own future change.

## Implementation

- **Port source is automikk at the pinned ref `af7ec71`** (#211; the later
  #212 touched no engine files, so this equals upstream HEAD for every
  target). All three files are ported with
  `python3 tools/port.py apply --source /Users/mikkelbergmann/projects/automikk --ref af7ec71 --include <automikk path> --dest .`
  from the worktree root. Rejected: re-implementing from the spec — the
  upstream implementation is tested and reviewed; re-derivation invites
  drift.
- **Overwrite purity was verified by a scratch port before planning**:
  `video_ingest.py`'s last pre-#211 upstream touch (#191) predates the
  engine-port snapshot and is already in shipd, so its overwrite is the pure
  #211 delta (5 replaced lines) and ports residual-free; the test file is a
  whole-file add, residual-free.
- **`SKILL.md` overwrite knowingly reverts a local brand fix and the task
  restores it.** Upstream still carries two bare `am:video-ingest` forms
  (lines 28–29) that `epic-video-brief` already fixed in shipd; `port.py
  apply` re-emits them and exits 2 naming exactly those lines. Per the
  standing ruling recorded in that change, the task re-fixes both lines to
  `s:video-ingest` after the apply. Cleanliness is then confirmed with
  `port.py verify --dest .` (grep its output for the file — it must not
  appear); re-running `apply` is NOT a valid check, since apply rewrites from
  source and reverts the fix.
- **Delta specs are token-mapped ports of automikk's archived deltas**
  (`.am/completed/2026-08-14-video-cursor-grounding/specs/`), both pure
  `## ADDED Requirements` — no `base:` hashes to rebase. The `am-video-ingest`
  capability folder maps to `shipd-video-ingest`.
- **Plugin version bumps once** in `plugins/s/.claude-plugin/plugin.json`
  (repo rule: every `plugins/s/` change bumps in the same PR).
- Risk: the ported tests could pass vacuously against the old code. Guard:
  test-first ordering — the test file lands first and the new cases must be
  observed failing (baseline suite is 101 tests OK) before the implementation
  is ported.
