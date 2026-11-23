<!-- doc-type: how-to -->

# Video ingest

A **video intent brief** turns a screen recording into a list of requested
changes. Each intent rests on the transcript words that expressed it. Each
intent also cites the frame that was on screen when those words were spoken.

The engine installs the brief under the content directory's `video/` folder,
at `video/<slug>/brief.md`. An epic links the brief from its `## Video`
section, and [`/s:epic`](epics.md) reads it as context. A plan reads the brief the same
way.

`/s:video-ingest` stages the recording, grounds the intents, installs the
brief, and stops. It never plans or builds anything from what it finds.

## When to use it

Run `/s:video-ingest` when someone recorded their feedback instead of writing
it: a walkthrough of a screen, with spoken requests for changes. The brief
turns that recording into intents a planner can act on.

[`/s:plan`](plan.md) also accepts a recording directly; [Plan a change](plan.md) covers
that path.

## How to run it

Pass a video path, or the slug of a bundle that already exists:

```sh
/s:video-ingest ~/Movies/review-walkthrough.mov
/s:video-ingest review-walkthrough
```

With a video path, the skill ingests the recording into a new bundle. With a
slug, it reads that bundle again and skips the ingest.

### The stages

The skill runs six stages, in order:

1. **Preflight** — it checks for the two required tools, `ffmpeg` and `uv`.
   When either tool is missing, the skill names it and stops.
2. **Bundle** — it extracts the audio, transcribes it, and extracts the
   keyframes. Given a slug, it resolves the existing bundle instead.
3. **Read** — it reads the transcript and the frame index. Those two files are
   the whole evidence base.
4. **Extract** — it lists the actionable changes the speakers request.
5. **Ground and compose** — it grounds each intent on a frame, resolves
   conflicts, and writes the brief.
6. **Install** — the engine validates the brief and installs it, or refuses
   it.

When the transcript holds no actionable intent, the skill reports that and
stops. It installs nothing, because a brief needs at least one intent.

### The grounding rules

- **Anchor on words.** The skill anchors each intent on the specific
  transcript words that express it, at the first word's start time.
- **Cite the nearest frame.** The frame closest to that anchor time becomes the
  intent's citation.
- **Trust the frame.** Where the frame contradicts the transcript, the brief
  states what the frame shows and notes the transcript's wording apart.
- **Read the pointer crop.** Where a cited frame records the cursor, the skill
  names the element under it. Without that record, it makes no claim about
  the pointer.
- **Resolve conflicts by recency.** The latest statement about a target wins.
  The brief keeps the earlier statement with its timestamp.
- **Ask what recency cannot order.** Two statements that recency cannot order
  go under `## Open questions`, with both positions and timestamps.

Each intent heading states the requested change as an imperative. When a
speaker complains about a current state, the heading names the change away
from it.

## Reference

### The bundle's files

| file | content |
| --- | --- |
| `manifest.json` | the bundle facts, including the source recording's name |
| `transcript.json` | a `words` array of `{start, end, text}` entries |
| `frames.json` | a `frames` array: `file`, `time`, `reason`, and provenance |
| `frames/` | the extracted keyframe images |

### The brief's sections

The brief opens with a `# <title>` line. A `Video:` line follows it directly
and names the source recording. The optional `Bundle:` and `Project:` lines
come next.

| section | content |
| --- | --- |
| `## Intents` | one `### <intent>` heading per change, each with a `[n]` citation |
| `## Open questions` | optional; conflicts that recency cannot order |
| `## Sources` | numbered entries, each opening with an `[HH:MM:SS]` timestamp |

No source entry names a speaker.

### Listing briefs

List the installed briefs, across the root and its worktrees:

```sh
shipd list video
```

An epic links a brief as `- [<title>](../../video/<slug>/brief.md)` under its
`## Video` heading.
