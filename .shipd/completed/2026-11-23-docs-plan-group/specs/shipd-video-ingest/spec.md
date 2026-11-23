## ADDED Requirements

### Requirement: Video ingest user documentation
id: video-ingest-user-docs

The repository SHALL provide `docs/video-ingest.md` as the main page for
`/s:video-ingest`, conforming to the shipd documentation standard with the
marker `how-to` on its first line and a total line count within that type's
cap.

The page SHALL follow the main-page shape: opening paragraphs saying what a
video intent brief is, then `## When to use it`, `## How to run it`, and a
closing `## Reference`, in that order. It SHALL cover: the brief as a cited
artifact installed under the content directory's `video/` folder that an epic
or a plan reads; the `/s:video-ingest <video-or-slug>` invocation with both
argument forms; the preflight's required tools, `ffmpeg` and `uv`; the
stages (preflight, bundle, read, extract, ground and compose, install); the
stop with nothing installed when the transcript holds no actionable intent;
the grounding rules (each intent anchored on transcript words, cited to its
nearest frame, conflicting statements resolved by recency); the bundle's
files; the brief's sections (`## Intents`, `## Open questions`,
`## Sources`); and `shipd list video` as the way to list installed briefs.
It SHALL state in one sentence that `/s:plan` accepts a recording, and link
`docs/plan.md` for the detail.

Every interactive command on the page SHALL invoke the `shipd` binary or name
a `/s:` skill — never an engine script path.

#### Scenario: Page follows the main-page shape
- **WHEN** the level-2 headings of `docs/video-ingest.md` are listed
- **THEN** they are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order

#### Scenario: Page covers the skill
- **WHEN** `docs/video-ingest.md` is inspected
- **THEN** it names the `/s:video-ingest` invocation with a video path and a
  bundle slug, the `ffmpeg` and `uv` requirement, the stages, the no-intent
  stop, the grounding rules, the brief sections, and `shipd list video`

#### Scenario: Page passes the lint
- **WHEN** `docs_lint.py` runs over `docs/video-ingest.md`
- **THEN** it exits 0 with the page marked `how-to`, and the page names no
  `video_ingest.py`, `spec_status.py`, or `spec_emit.py` path
