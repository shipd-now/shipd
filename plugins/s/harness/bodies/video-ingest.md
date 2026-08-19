<!-- description: Turn a screen recording into a grounded, cited intent brief installed through the engine. -->
# /s:video-ingest — recording → grounded, cited intent brief

Turn a recording's bundle — a transcript plus indexed frames — into a video
intent brief whose every intent is anchored to the words that expressed it and
cited to the frame that was on screen. You stage, read, ground, compose,
install, and stop; you plan and build nothing from what you find.

<!-- include:preamble -->

The ingest CLI sits beside the engine scripts:
`V="$S/../../video-ingest/scripts/video_ingest.py"`.

## 1. Preflight the toolchain

`python3 "$V" doctor` exits non-zero only when a **required** tool is missing;
a cold model cache is reported and never fails the check. A missing required
tool stops the flow — attempt nothing against a toolchain already flagged.

## 2. Obtain the bundle

- **A video path** → `python3 "$V" ingest <path> [--slug <slug>]`, which runs
  audio extraction, speech recognition, and frame extraction, then prints the
  bundle's absolute directory.
- **A slug whose bundle already exists** → do not re-ingest. Resolve it with
  `python3 "$V" path <slug>`, then verify that directory and its
  `transcript.json` actually exist: `path` performs no existence check of its
  own and exits 0 for any string, so its exit code is never evidence.

Either way the bundle holds `manifest.json`, `transcript.json`, `frames.json`,
and a `frames/` directory. Those two JSON files are the whole evidence base —
no audio playback and no re-transcription.

## 3. Extract candidate intents from the transcript

`transcript.json` is a flat `words` array of `{start, end, text}` entries.
Read it and form the actionable changes the speakers asked for, anchoring each
candidate on the word or short run of words that expresses it and taking that
word's `start` as the anchor. Where the transcript carries no actionable
intent, report that and stop **without installing** — the grammar requires at
least one intent, so a brief with none is a non-output, not a degraded one.

## 4. Ground each intent on its nearest frame

Scan `frames.json` for the entry whose `time` is closest to the anchor; that
entry is the intent's citation. Open only the frames the candidates anchor to
— reading a whole bundle's images before reasoning starts spends context on
frames no intent ever cites. Where a cited entry carries a `cursor` object,
open its zoom crop too and name the element under the pointer; where it
carries none, make no claim about where the speaker was pointing.

**The frame outranks the transcript wherever they disagree** — speech
recognition mishears domain and interface vocabulary, so state what the frame
shows and note the transcript's wording separately, never repeating a misheard
term as though it were fact.

## 5. Name the change, never the observed state

Every `### ` intent heading is read downstream as an instruction, so it states
the requested change as an imperative. A speaker describing a current state
with disapproval — "that's weird", "it doesn't look right" — wants to move
**away** from it: the heading names the destination and the complaint belongs
in the body as evidence. Re-read each heading alone and ask whether applying
it verbatim would satisfy the speaker or reproduce their complaint; rewrite it
when the answer is the second.

Where the recording states conflicting intents about one target, the **latest**
statement is the outcome and the superseded one stays in the brief with its
timestamp. Where recency cannot order them, record both under
`## Open questions` and resolve neither.

## 6. Compose and install through the engine

The brief opens with a `# <title>` line, carries its `Video:` metadata line
immediately underneath with **no blank line between them**, then a `## Intents`
section of `### ` headings each bearing at least one `[n]` citation, and a
`## Sources` section whose every numbered entry opens with a zero-padded
`[HH:MM:SS]` timestamp. `Video:` names the source recording from the bundle's
manifest, never the bundle slug.

Author into a staging file outside the content directory, then install it —
never write into the tree yourself and never construct its path:

```sh
python3 "$S/spec_emit.py" video <slug> --from <staging-file>
```

The engine validates in process and removes whatever it installed on any
finding, so fix the staged file and re-run until it exits 0; add `--replace`
only to overwrite an installed brief. Read it back with
`python3 "$S/spec_status.py" cat video <slug>`.

## 7. Report, then stop

Report the installed brief's slug and location, summarize the intents one line
each, and note anything routed to `## Open questions`. Then point at `/s:epic`,
which reads briefs linked from an epic's `## Video` section as
pre-investigation context. This command opens no epic and plans no change.
<!-- if:file-references -->
The full brief grammar, its metadata rules, and the linter's findings are
written out in {refs}/video-ingest.md — read it before composing.
<!-- else -->
The full brief grammar is not available as a separate file here. Say so before
composing, state that you would have read the video-ingest reference for the
exact skeleton, and compose from the shape above — then let the emit engine's
findings correct you, since it installs nothing the grammar rejects.
<!-- end -->
