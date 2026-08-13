# video-ingest-skill
Status: verified
Epic: video-ingest
Theme: developer-experience

## Idea

Add the `/s:video-ingest` skill: read a recording's bundle, extract what the
speaker actually wants changed, and install it as a lint-clean intent brief.

### Motivation

The pipeline produces a speaker-attributed transcript and indexed frames, and
the brief artifact exists to receive them, but nothing reads one and writes the
other — the epic's whole output is currently unreachable.

### Details

- Add `plugins/s/skills/video-ingest/SKILL.md`, turning the existing
  scripts-and-tests directory into a loadable skill.
- Stage the flow: preflight, bundle (ingest a video or reuse a slug), read the
  transcript, ground candidate intents on frames, arbitrate, compose, install.
- Anchor each intent on transcript **words** and cite the nearest indexed frame.
- Name speakers from the transcript, falling back to the diarization label.

Affected capabilities: `shipd-video-ingest` (added). Impact:
`plugins/s/skills/video-ingest/SKILL.md`, a documentation-only `--root`
placement correction in `plugins/s/skills/research/SKILL.md` (see the
Implementation decision below), and the plugin version in
`plugins/s/.claude-plugin/plugin.json`. No engine scripts change and no new
dependencies.

### Non-goals

- No audio sampling, `afplay` playback, or roster persistence — that is
  `video-ingest-speakers`; this member only mines names already spoken.
- No `/s:plan` entry point or epic routing — `plan-video-entry` owns that.
- No `/s:epic` brief consumption — `epic-video-brief`.
- No cursor grounding.
- No change to `video_ingest.py`, the bundle contract, or the brief grammar;
  both are already shipped and this member composes to them.
- No new eval case (see the Implementation decision below).

## Implementation

**`/s:research` is the template.** Its capability spec is three requirements —
staged pipeline, engine-mediated emission, cited composition — and this skill is
the same shape with a bundle in place of web search. Reusing that structure
keeps one editorial convention across both document-producing skills. The brief
grammar it composes to is already shipped and enforced at install time
(`.shipd/README.md`, "Video intent briefs"), so this member invents no format.

**Intents anchor on words, never on segments.** `transcript.json` segments split
only at speaker changes, so on a single-speaker recording one segment can span
40 seconds — useless for choosing which frame was on screen. Each intent
therefore anchors on the `start` of the specific words that express it, and the
citation resolves to the nearest entry in `frames.json`. Rejected: anchoring on
segments (too coarse) and re-deriving timings from the audio (the pipeline
already computed them).

**Frames are read selectively, because context is the scarce resource.** A
48-second recording yields ~23 frames at 1462×1350; reading all of them before
reasoning starts spends a large share of the window on images that no intent
references. The skill forms candidate intents from the transcript first, then
reads only the frames nearest those anchors. Rejected: reading every frame up
front — simpler, and wasteful in exactly the case the epic cares about (longer
recordings).

**The frame is authoritative over the transcript where they disagree.** ASR
mishears domain and UI vocabulary — on the reference recording it produced
`sensor aligned` for what the frame plainly shows as a centre-aligned list, and
`auto mic` for `shipd`. Where a frame contradicts the transcript, the brief
states what the frame shows and notes the transcript's wording, rather than
propagating a misheard term into a spec.

**Speaker naming splits cleanly from the sibling member.** This skill mines
names already present in the transcript — self-introduction and direct
address — and otherwise uses the diarization label as the name, so
`## Speakers` is always satisfiable. `video-ingest-speakers` later adds audio
sampling and persistence over the same section. Rejected: an interactive naming
round here, which would duplicate that member.

**Arbitration follows the epic's D11 exactly.** Where two speakers state
conflicting intents about the same target, the configured decider's *latest*
statement is the outcome and every superseded statement is retained with its
speaker and timestamp. **Where no decider is configured, a conflict becomes an
entry under `## Open questions` — never a silent pick.**

**Source timestamps are zero-padded `HH:MM:SS`.** The shipped lint requires a
bracketed three-field timestamp, while transcript offsets are raw seconds; a
sub-hour utterance formatted naively renders as `0:05:12` and fails the install.
The skill formats explicitly before composing.

**No new eval case, deliberately.** `AGENTS.md` asks for a local eval run on
changes touching a skill's `SKILL.md`. The existing cases exercise `/s:plan`,
which this member does not modify, so they cannot regress on it; and a case for
this skill would need a video fixture — a multi-megabyte binary committed under
`evals/cases/`. The manual verification task against the real recording is this
member's equivalent, and it is mandatory rather than optional.

**The `--root` correction reaches `/s:research` too, on the user's explicit
instruction.** Validation refuted the emission scenario: both skills documented
`spec_emit.py <verb> <slug> --from <file> --root <repo-root>`, but `--root` is a
top-level option in `spec_emit.py` and `spec_status.py`, so the documented
command fails with `unrecognized arguments` before reaching the linter. The
defect originated in `research/SKILL.md` and was inherited verbatim here. It is
documentation-only — no `shipd-research` requirement mentions `--root`, so no delta
against that capability is needed — and fixing only the copy would leave the
original broken for the next skill to inherit.

Risk: intent extraction is model judgement with no mechanical test, so a green
lint proves only that the brief is well-formed, not that it captured what the
speaker meant. Guarded by requiring the verification task to compare the emitted
intents against the four changes actually requested in the reference recording
(button styling, filter alignment, `add filter` capitalisation, header
consistency) and to record any missed or invented intent in the PR description.
