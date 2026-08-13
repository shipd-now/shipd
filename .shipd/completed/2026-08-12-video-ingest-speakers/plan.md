# video-ingest-speakers
Status: verified
Epic: video-ingest
Theme: developer-experience

## Idea

Let a person put real names to the voices in a recording: play a short sample
per unidentified speaker, ask once, and remember the names for next time.

### Motivation

Diarization emits arbitrary labels and the shipped skill can only mine names
that happen to be spoken aloud, so a multi-speaker brief attributes every
intent to `speaker_00`-style labels that tell a reader nothing about who
decided what.

### Details

- Add a `samples` verb writing one representative audio clip per speaker label
  into the bundle's new `samples/` directory.
- Add a `merge-speakers` verb that relabels words, re-assembles segments, and
  records the merge in `manifest.json`.
- Add a `roster` verb persisting confirmed names to `build.video_speakers`.
- Replace the skill's never-interactive rule with a naming round that runs only
  when two or more labels remain unnamed after mining.

Affected capabilities: `video-pipeline` (modified), `shipd-video-ingest`
(modified). Impact: `plugins/s/skills/video-ingest/scripts/video_ingest.py`,
`plugins/s/skills/video-ingest/SKILL.md`, the suite under
`plugins/s/skills/video-ingest/tests/`, and the plugin version in
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No speaker embeddings, voiceprints, or biometric data on disk — the roster
  stores names only (epic D10).
- No cross-recording automatic identification; the roster is offered as
  candidates, never auto-applied to a label.
- No change to diarization itself, the spurious-turn filter, ASR, or frames.
- No naming round for a single unnamed label — the shipped label-as-name
  fallback continues to cover it.
- No re-derivation of frames after a merge; frames carry no speaker attribution.

## Implementation

**The split follows what is mechanically testable.** Sample extraction, label
merging, and roster persistence are `video_ingest.py` verbs driven through the
existing injectable runner, so they are unit-tested with no `ffmpeg` present.
Playback and the question round are inherently interactive and live in
`SKILL.md`. This mirrors how the epic already divides the pipeline from the
skill.

**A sample is clamped to the audio that exists, not assumed to be five
seconds.** On the reference bundle `speaker_00` holds 1.8 seconds in total, so
a fixed five-second cut would run past the speaker's own audio into someone
else's. The verb selects the label's longest turn, centres the window on it,
and clamps the duration to `min(SAMPLE_SECONDS, turn_duration)` — the sample is
always that speaker and only that speaker.

**Merging rewrites `transcript.json`, and the rewrite is recorded.** Where the
naming round gives two labels the same name, `merge-speakers` relabels the
affected words, re-runs the existing segment assembly (which already coalesces
consecutive same-speaker words, so no adjacent duplicate segments survive), and
writes the file back. Mutating the diarizer's output is a real cost, accepted
deliberately: `manifest.json` records a `speaker_merges` entry naming which
labels were folded into which name, so the change is auditable, and re-running
`ingest --force` regenerates the bundle from the source video, which remains
the backup. Rejected: leaving both labels in place with one name (visible but
duplicated downstream) and merging only in the brief (the brief and bundle
would then disagree on how many speakers exist).

**The naming round is gated on two or more unnamed labels.** A solo recording —
the common "here is what I want changed" case — is never interrupted, and the
shipped label-as-name fallback still covers it. The gate is on *unnamed* labels
specifically, so a recording where mining already recovered every name asks
nothing either.

**Roster persistence is a verb, not the skill writing config by hand.**
`roster --add <name>…` merges names into the resolved project `.shipd-config.json`
under `build.video_speakers`, preserving every other key and creating the file
only if absent. A skill editing a user's configuration through free-form file
writes is exactly the kind of side effect the engine-mediated rule exists to
prevent. The roster is offered as candidate answers in the naming round and is
**never auto-applied** to a label — arbitrary diarization labels carry no
identity across recordings, so a stored name is a suggestion, not a mapping.

**`afplay` is the player, and its absence is not fatal.** It ships at
`/usr/bin/afplay` on macOS. Where playback fails or the tool is missing, the
round still runs — the skill reports that the sample could not be played and
falls back to naming from the transcript excerpt around that speaker's longest
turn, because a failed audio cue must not block a brief.

Risk: a user who names two genuinely different speakers identically will merge
two real voices into one, silently losing the distinction. Guarded by requiring
the naming round to state, before asking, which label holds how many seconds of
speech, and by the manifest record making the merge visible after the fact.
