# epic-video-brief
Status: verified
Epic: video-ingest

## Idea

Port automikk's `epic-video-brief` change — the optional `## Video` epic
section, its lint validation, and the epic-authoring flow that consumes a video
intent brief — into shipd's engine, closing a gap the engine-port snapshot
missed.

### Motivation

The `epic-video-brief` member of the `video-ingest` epic shipped in automikk
(PRs #209/#210) after shipd's engine-port snapshot was taken, so shipd's
linter, epic skill, and spec grammar know nothing of the `## Video` section and
the member sits unplanned on the board. Porting the finished, upstream-verified
implementation closes the gap without re-deriving settled work.

### Details

- Generalize `spec_lint.py`'s epic research-link check into a shared
  `_check_epic_link_section` helper and validate the optional `## Video`
  section against the content directory's `video/` folder.
- Port the Video-section unittest additions into `test_spec_lint.py`.
- Port the `/s:epic` skill's video-brief consumption flow and the
  `/s:video-ingest` skill's cross-references.
- Document the `## Video` grammar in `.shipd/README.md`.
- Bump the plugin version.

Affected capabilities: `shipd-epic`, `shipd-spec-format`, `shipd-spec-lint`
(modified — ADDED requirements). Impact:
`plugins/s/skills/build/scripts/spec_lint.py`,
`plugins/s/skills/build/tests/test_spec_lint.py`,
`plugins/s/skills/epic/SKILL.md`, `plugins/s/skills/video-ingest/SKILL.md`,
`.shipd/README.md`, `plugins/s/.claude-plugin/plugin.json`. No new
dependencies — the stdlib-only constitution rule holds.

### Non-goals

- No `video-cursor-grounding` port — the epic's other unplanned member is
  planned separately after this ships; its `video-ingest/SKILL.md` edits stack
  on this change's, which is why this port is pinned to automikk ref
  `dbe12a4`, not HEAD.
- No changes to `video_ingest.py` or the ingest pipeline.
- No porting of automikk's archived artifacts for this member — shipd's own
  pipeline records this change, and the archive entry it produces on merge is
  the member's record.
- No re-litigation of upstream design decisions — the port carries them as
  shipped and review-dispositioned in automikk.

## Implementation

- **Port source is automikk's squashed delta `48648a8..dbe12a4`** (#209 plus
  its #210 review disposition) in `/Users/mikkelbergmann/projects/automikk`,
  read per file with
  `git -C /Users/mikkelbergmann/projects/automikk diff 48648a8..dbe12a4 -- <file>`.
  Rejected: re-implementing from the spec — the upstream implementation is
  tested and review-dispositioned; re-derivation invites drift.
- **Two port mechanics, chosen per file by divergence:**
  - *Clean overwrite* for files untouched in shipd since the engine-port
    snapshot: `plugins/s/skills/epic/SKILL.md` (automikk's last pre-#209 touch
    was #48, pre-snapshot) and `plugins/s/skills/video-ingest/SKILL.md` (#195,
    pre-snapshot). Overwrite via
    `python3 tools/port.py apply --source /Users/mikkelbergmann/projects/automikk --ref dbe12a4 --include <automikk path> --dest .`,
    which token-maps paths and contents. The ref is pinned to `dbe12a4` so
    #211's cursor-grounding edits to `video-ingest/SKILL.md` cannot leak in.
  - *Manual delta application* for files shipd modified after the snapshot
    (`oracle-qa-ledger`, 411853a): `spec_lint.py`, `test_spec_lint.py`,
    `.shipd/README.md`. The upstream hunks are semantically independent of
    oracle-qa-ledger's additions (`check_plan_qa_section` near line 369, a
    regex near line 91): apply the upstream edits by hand under the token map
    (anchored `am` forms → `s`/`shipd`, `.am/` → `.shipd/`, `/am:` → `/s:`),
    leaving oracle-qa-ledger's code untouched.
- **Upstream naming carries over unchanged**: `RESEARCH_LINK_RE` becomes
  `EPIC_LINK_RE`; `_check_epic_research` becomes
  `_check_epic_link_section(root, path, text, errors, header, folder, noun)`,
  called once with `("## Research", "research", "research file")` and once with
  `("## Video", "video", "video intent brief")`. Rejected: a copy-pasted
  second checker — the upstream refactor already unified the two sections.
- **Delta specs are token-mapped ports of automikk's archived deltas**
  (`.am/completed/2026-08-14-epic-video-brief/specs/`), all pure
  `## ADDED Requirements` — no `base:` hashes to rebase.
- **Plugin version bumps once** in `plugins/s/.claude-plugin/plugin.json`
  (repo rule: every `plugins/s/` change bumps in the same PR).
- Risk: the manual `spec_lint.py` merge drifts from upstream. Guard:
  test-first ordering — the ported tests land first and fail, then the
  implementation makes them pass, and the full engine suite (143 tests green
  pre-change via `python3 -m unittest discover -s plugins/s/skills/build/tests`)
  is the completion barrier.
