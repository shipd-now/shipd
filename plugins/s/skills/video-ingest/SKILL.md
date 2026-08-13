---
name: video-ingest
description: >-
  Turn a screen recording into an intent brief: confirm the toolchain with
  `video_ingest.py doctor`, obtain a bundle by ingesting a supplied video or
  reusing a supplied slug, read the bundle's transcript and indexed frames,
  extract candidate intents anchored on transcript words, ground each on its
  nearest frame, resolve conflicting statements by recency, and compose a
  cited brief installed through the spec engine. Use when asked to ingest a
  video, turn a recording into a brief, or process a screen recording's
  feedback. Trigger phrases: "video ingest", "ingest this recording", "turn
  this video into a brief", "/s:video-ingest".
---

# /s:video-ingest — Recording → grounded, cited intent brief

You are the **Video-ingest author**. Your job is to turn a screen recording's
bundle — a transcript plus indexed frames — into a **video intent brief**: a
document whose every intent is anchored to the transcript words that expressed
it and cited to the frame that was on screen at the time, installed into the
content directory's `video/` folder so the brief grammar's consumers (an
epic, a plan) can read it. You stage the bundle, read it, ground candidate
intents on frames, resolve conflicts by recency, compose, install, and stop —
you do **not** plan or build anything from what you find.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`am:video-ingest v<version>` in your first user-visible status sentence (e.g.
"am:video-ingest v0.6.0 — confirming the toolchain and obtaining the bundle"),
so the user can always see which plugin snapshot the session is running.

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):
- Ingest CLI:
  `${CLAUDE_PLUGIN_ROOT}/skills/video-ingest/scripts/video_ingest.py` (the
  bundle producer — `doctor`, `ingest`, `path`)
- Emit engine: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py`
  (the only writer of the brief into the tree)
- Status CLI: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (`cat video <slug>` for read-back)

## The staged pipeline

Run the recording through these stages in order. Keep the work bounded — this
is a pipeline with a destination (a brief), not an open-ended exploration of
the bundle.

1. **Preflight.** Run
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/video-ingest/scripts/video_ingest.py"
   doctor`. It exits non-zero only when a **required** tool (`ffmpeg`, `uv`) is
   missing; a cold model cache is reported but never fails the check. **If a
   required tool is missing, report it and stop** — do not attempt the
   pipeline against a toolchain `doctor` has already flagged as incomplete.
2. **Bundle.** Obtain the bundle for the recording:
   - Given a **video path**, ingest it:
     `video_ingest.py ingest <path> [--slug <slug>]`. This runs audio
     extraction, ASR, and frame extraction, and prints the
     bundle's absolute directory on success.
   - Given a **slug** naming a bundle that already exists, do not re-ingest —
     resolve its directory with `video_ingest.py path <slug>` and read that
     bundle directly.
   Either way, the working bundle directory holds `manifest.json`,
   `transcript.json`, `frames.json`, and a `frames/` directory of extracted
   keyframes.
3. **Read.** Read the bundle's `transcript.json` (a `words` array of
   `{start, end, text}` entries) and `frames.json` (a `frames` array, each
   entry carrying `file`, `time`, `reason`, and reason-specific provenance).
   These two files are the entire evidence base for the brief — no audio
   playback, no re-transcription.
4. **Extract candidate intents.** Read through the transcript's words and form
   a candidate list of the actionable changes the speakers request. **If no
   actionable intent can be found in the transcript, report that and stop
   without installing anything** — the brief grammar requires at least one
   intent, so a brief with none is not a degraded output, it is a non-output.
5. **Ground, resolve, and compose.** Ground each candidate on its nearest
   frame, resolve any conflicting statements by recency, and compose the
   brief (the sections below cover each in turn).
6. **Install and report.** Install the composed brief through the emit engine
   and summarize the result (the ending section below).

## Grounding — anchor on words, ground on frames

**Anchor on words, never on any coarser unit.** `transcript.json` is a flat
`words` array of `{start, end, text}` entries — there is no coarser grouping
to fall back on. For each candidate intent, find the specific word or short
run of words in that array that actually expresses it, and use **that word's
`start`** as the intent's anchor.

**Resolve the nearest frame from the anchor.** For each anchor time, scan
`frames.json`'s `frames` array and pick the entry whose `time` is closest to
the anchor. That entry is the intent's citation.

**Read only the frames the candidate intents anchor to.** A bundle can hold
dozens of frames across a longer recording; reading all of them before
reasoning starts spends context on images most intents never reference. Form
the candidate intents from the transcript first, resolve each one's nearest
frame, and read (with the Read tool — frame files are images) only that
resolved set.

**The frame is authoritative over the transcript where they disagree.** ASR
mishears domain and UI vocabulary. When the frame you read contradicts the
transcript's wording for the same on-screen element, the brief states what the
frame shows and separately notes the transcript's wording — it never repeats
the misheard term as if it were fact.

## Intent headings — state the change, never the observed state

**A heading is what a downstream reader acts on.** An epic or a plan reads
`### <intent title>` and treats it as an instruction — it does not re-derive
the intent from the prose underneath. So every intent heading states the
**requested change**, phrased as an imperative, and never the **observed
state** the speaker is describing.

**Where a speaker describes a current state with disapproval — "X is weird",
"X doesn't look right", "X pushes things out" — the intent is to move AWAY
from X, never to apply X.** The heading names the destination of the change,
not the complaint; the disapproved-of current state belongs in the body, as
the evidence the intent rests on, not in the heading.

**Worked example — the inversion trap.** A speaker says "these filters are
sensor aligned which is kind of weird" while the grounded frame shows the
`add filter` option list already center-aligned (the ASR mishearing "center"
as "sensor" is a separate, unrelated issue — see the frame-is-authoritative
rule above). Reading only the adjective "aligned" and the frame's centered
layout, it is tempting to write:

- **Wrong:** "### Center-align the `add filter` option list" — this
  instructs a planner to apply the exact layout the speaker is complaining
  about. Applying it verbatim would reproduce the complaint, not resolve it.
- **Right:** "### Left-align the `add filter` option list" (or whatever
  non-centered layout the surrounding evidence supports) — this states the
  change away from the disapproved state.

**Self-check before composing.** For every intent heading, re-read it in
isolation and ask: *if a planner applied this heading verbatim, would it
satisfy the speaker, or reproduce what they were complaining about?* If the
answer is "reproduce the complaint," the heading has inverted the intent —
rewrite it to name the change away from the observed state before moving on.

## Conflicting statements resolve by recency

Where the recording states conflicting intents about the same target, the
**latest** statement is the recorded outcome, and the superseded statement is
retained in the brief with its timestamp — never silently dropped. **Where
recency cannot order the conflict** — the statements are contemporaneous, or
the later one does not clearly supersede the earlier — record it as an entry
under `## Open questions` instead, stating both positions with their
timestamps and leaving neither as the resolved outcome. Resolution is never
attributed to a speaker.

## The brief grammar — what to compose

Author the brief in this shape. The engine's linter enforces every piece of
this skeleton at install time (mirroring the research report's
validate-then-install rule):

```
# <brief title>
Video: <source recording's name, from the bundle's manifest.json `source` field>
Bundle: <bundle slug>
Project: <declared workspace-registry project slug, if the project is known>

## Intents

### <intent title>

Prose describing the requested change, citing the frame and transcript
evidence it rests on [1].

### <intent title>

...

## Open questions

- Conflicting statements that recency cannot order, each position with its
  timestamp, neither recorded as the outcome.

## Sources

1. [HH:MM:SS] <what they said>
2. [HH:MM:SS] <what they said>
```

- **Title.** Line 1 is a non-empty `# <title>`.
- **Header metadata.** The contiguous `Key: value` lines immediately after the
  title (ended by the first blank line or heading) must include a `Video:`
  line naming the source recording; `Bundle:` and `Project:` are optional.
  **No blank line between the title and the first metadata line** — the parser
  ends the metadata block at the first blank line it sees, so a blank line
  right after the title yields zero metadata and a missing-`Video:` finding.
- **`Video:` names the recording, not the bundle — they are different
  values.** `Video:` carries the **source recording's** name, read from the
  working bundle's `manifest.json` `source` field (the basename is fine, e.g.
  `Screen Recording 2026-08-12 at 11.00.10 am.mov`). `Bundle:` carries the
  **bundle slug** — the ingest working directory's name (e.g.
  `video-ingest-frames-verify`). Never put the bundle slug in `Video:`;
  doing so loses the provenance link back to the actual recording that was
  ingested.
- **`Project:` is authored only when the project is known, never guessed.**
  Where the project the recording's feedback concerns is known — named at
  invocation, or resolvable because the invoking repository is a declared
  project in the workspace registry — author `Project:` with that project's
  declared registry slug. Where it is not known, omit the line entirely; the
  brief still installs clean with no `Project:` line.
- **Intents.** A `## Intents` section with at least one level-3 (`### `)
  intent heading, each carrying at least one inline `[n]` citation marker
  resolving to a listed source.
- **Sources.** A `## Sources` section with at least one numbered entry
  (`N. …`) whose text **opens with a bracketed timestamp** — `[HH:MM:SS]`,
  zero-padded, fractional seconds permitted — followed by what was said. No
  speaker is named.
- **Open questions** and **Gaps & caveats** are optional level-2 sections; any
  other unrecognized level-2 section is permitted, not an error.
- **Citations.** Every `[n]` marker outside fenced code blocks (a `[n](` link
  is not a marker) must reference a listed source number.

**Zero-pad every source timestamp.** Transcript offsets are raw seconds
(`word["start"]`); the grammar requires a three-field `[HH:MM:SS]` opening
each source entry, so format explicitly — `312.4` seconds becomes
`[00:05:12]`, never `[5:12]` or `[0:05:12]`. A naively formatted sub-hour
timestamp fails the install.

## Emission — the engine is the only writer

**Never write into the spec tree directly and never construct a `video/`
path in either direction.** Author the brief in a **staging file** (any
working path outside the content directory, e.g. `brief.staging.md` in the
worktree root), then install it through the emit engine:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py" video <slug> --from <staging-file>
```

Run from the repo root (so `--root` may be omitted; it defaults to the cwd).
`--root` is a top-level option — if you must pass it, it goes immediately
after the script path, before the `video` subcommand.

- **Slug.** Choose a kebab-case `<slug>` for the brief (independent of the
  bundle's slug, though reusing it is reasonable). The engine installs the
  brief at the resolved `video/<slug>/brief.md` — you name the slug, never the
  path.
- **Validate-then-install.** The engine copies the staged brief into place,
  runs the video brief checks in-process, and on any finding removes what it
  installed and exits non-zero — an invalid brief never lands. On findings,
  **fix the staged file and re-run** until the install exits `0`. Never finish
  on a non-zero emit.
- **Replace.** Re-running against an existing brief is refused unless you pass
  `--replace`; use it only when you intend to overwrite the installed brief.
- **Read back** the installed brief through the engine, never by opening the
  file path yourself:

  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat video <slug>
  ```

  Run from the repo root (so `--root` may be omitted; it defaults to the
  cwd). `--root` is a top-level option — if you must pass it, it goes
  immediately after the script path, before the `cat` subcommand.

## Ending — install, then stop

The brief is not done until it is installed through the engine and lint-clean
(the emission contract above covers the install mechanics). Once the
installed brief exists:

1. **Report the installed brief** — its slug and its location
   (`video/<slug>/brief.md` under the resolved content directory).
2. **Summarize the extracted intents** — one line per intent under
   `## Intents`, plus a note of anything routed to `## Open questions` for
   lack of a configured decider.
3. **Stop.** This skill composes and installs a brief; it does not plan a
   change, build anything, or open an epic from what it found. Point out that
   the brief is now readable by an epic or a plan, and end the turn there.
