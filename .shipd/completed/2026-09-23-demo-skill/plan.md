# demo-skill
Status: verified
Theme: developer-experience

## Idea

Add a `/s:demo` skill that produces a branded demo video from either a
browser session or a terminal session, routing to the right capture backend.

### Motivation

shipd records branded demos of browser apps but has no path for a terminal
one, so a CLI feature can only be demonstrated as text. The workspace team
wizard shipped without a video for exactly that reason.

### Details

- Add a `tape` verb to the drive CLI recording a terminal session with `vhs`
  and emitting the same recording-plus-timeline pair `record` emits.
- Derive that timeline's `holds` and `leadingCut` from tape comments, leaving
  dead air to the post-processor's existing spinner backstop.
- Report `vhs` in the drive CLI's `doctor` as a terminal-recording-only
  prerequisite, failing only when that tier is actually needed.
- Add the `/s:demo` skill and its harness body, routing browser subjects to
  `record` and terminal subjects to `tape`, both converging on `post`.
- Move the `record a demo` trigger phrase from the drive skill to this one.

Affected capabilities: `shipd-demo` (added), `drive-video` (modified),
`shipd-drive` (modified). Impact:
`plugins/s/skills/drive/scripts/drive.py`, a new tape module beside it,
`plugins/s/skills/demo/SKILL.md`, `plugins/s/harness/bodies/demo.md`,
`plugins/s/skills/drive/SKILL.md`, and
`plugins/s/skills/drive/tests/`. New external tool: `vhs`.

### Non-goals

- No change to `post`, the spinner backstop, the title card, or the badge —
  the terminal path reuses them exactly as the browser path does.
- No terminal mode inside `/s:drive`. Drive stays the browser engine and
  keeps its verification flow.
- No automated `vhs` install. The drive CLI's `--fix` stays scoped to the
  Playwright browser binary.
- No replacement for `/s:video-ingest`, which runs the opposite direction —
  a recording into a brief.

## Implementation

- **`post` is already medium-agnostic, so the terminal path reuses it
  untouched.** Verified by running it: a 12-second clip ffmpeg generated from
  a solid colour, with a hand-written timeline, branded to a 4.63-second
  output — leading cut, fast-forward, and title card all applied with no
  browser anywhere. The verb takes `<recording> [--timeline]` and resolves no
  target and no session, so the whole branding stage is shared by
  construction. Rejected: a second post-processor for terminal video, which
  would duplicate the badge and card rules and let the two media drift.
- **The tape supplies `holds` and `leadingCut` only; the backstop finds dead
  air.** Verified by running `post` with `spans: []` against the same clip: the
  spinner backstop produced a byte-identical 4.633-second result. A tape's
  `Sleep` directives describe intended pauses, not real command durations, so
  statically derived spans would drift from the recording they annotate.
  Rejected: computing spans from the tape's own timing, which is wrong
  whenever a recorded command takes longer than its author guessed.
- **Annotations ride in tape comments** (`#hold`, `#endhold`, `#ready`) so a
  tape stays a valid `vhs` file that `vhs` itself can run unchanged. Rejected:
  a sidecar annotation file, which would let the tape and its annotations fall
  out of step.
- **`vhs` is a third doctor tier, not a widened `--fix`.** It joins `ffmpeg`
  and `ffprobe` as recording-only, failing solely when a terminal recording is
  requested. Note for the executor: `video_ingest.py`'s doctor `--fix` *does*
  Homebrew-install its tools, so an installing `--fix` is an established house
  pattern — the drive CLI's narrower posture is a deliberate local choice this
  change preserves rather than a rule it obeys.
- **The skill is `/s:demo`, and it takes the `record a demo` trigger with
  it.** The drive skill's frontmatter drops that phrase; `demo`'s claims it,
  following `epic-autopilot`'s rule that a surrendered trigger is re-homed on
  the successor rather than deleted. `shipd-drive`'s `drive-skill-flow` names
  no trigger phrases, so this costs no delta there.
- Risk: `vhs` renders through `ttyd` and a headless browser of its own, so its
  output geometry is fixed by the tape rather than by the terminal running it.
  Guarded by keeping the tape the single source of geometry and failing loudly
  on a non-zero `vhs` exit rather than branding a partial capture.

## Questions and answers

### Q1: What is the skill called, and does drive keep its recording trigger?
- **Question:** A new skill will produce demo videos, routing between the
  browser path and a new terminal path. Two skills already compete for that
  name and trigger space: `/s:drive`, whose frontmatter claims `record a
  demo`, and `/s:video-ingest`, which runs the opposite direction. Options:
  (a) `/s:demo`, drive drops the trigger; (b) `/s:video`, drive drops the
  trigger; (c) no new skill, drive gains a terminal mode. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a) — `/s:demo`. It sidesteps the near-collision with
  `/s:video-ingest` and names the artifact rather than the medium, which
  matters because the skill covers both. `/s:drive` drops `record a demo` and
  `/s:demo` claims it, so exactly one skill answers to the phrase. Drive stays
  the browser engine, keeping `record` and `post` as verbs the new skill
  drives.
- **Queued:** q-demo-skill-name-and-drive-record-claim

### Q2: Where does the terminal path live, and who preflights vhs?
- **Question:** The terminal path needs `vhs`, which is not installed and not
  a shipd dependency. Options: (a) a `tape` verb in the drive CLI with `vhs`
  as a recording-only doctor entry and no automated install; (b) a separate
  script with its own tiered doctor whose `--fix` installs it; (c) the drive
  CLI with a widened `--fix`. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a) — a `tape` verb inside the drive CLI, beside
  `record`. `vhs` joins `ffmpeg` and `ffprobe` as a recording-only doctor
  entry, failing only when a terminal recording is requested; `--fix` stays
  scoped to the browser binary and the skill names `brew install vhs`. One
  toolchain and one preflight rather than a second to keep in step.
- **Queued:** q-demo-video-vhs-dependency-doctor-placement

## Readiness attestation

### Problem and motivation

shipd can brand a demo of a browser app but not of a terminal one, so CLI
features ship without video.

Evidence:

- `plugins/s/skills/drive/scripts/drive.py` exposes `record` against a
  Playwright target only; no verb captures a terminal.
- Capability `drive-video` covers action modules, post-processing, and
  branding, and names no terminal medium.

### Scope and non-goals

The change adds a capture verb, a timeline reader, a doctor tier, and a
routing skill. The shared post-processing and branding stage is untouched.

Evidence:

- In scope: `plugins/s/skills/drive/scripts/drive.py`, a new tape module,
  `plugins/s/skills/demo/SKILL.md`, `plugins/s/harness/bodies/demo.md`,
  `plugins/s/skills/drive/tests/`.
- Out of scope: `postprocess.py` and `record_worker.py` are not edited.

### Affected capabilities and files

Three capabilities carry the change: a new `shipd-demo` for the skill,
`drive-video` for the tape contract, `shipd-drive` for the doctor tier.

Evidence:

- Capability `shipd-drive`: `drive-doctor` (base 675c1d55ea61), hash from
  `spec_status.py base-hash`.
- Capability `drive-video`: `drive-postprocess` and `drive-brand-frames` are
  reused unchanged; the two new requirements sit beside them.
- Runnable premise: `drive.py post term-fake.mp4 --title terminal-path-probe`
  on an ffmpeg-generated solid-colour clip exited 0 and wrote
  `term-fake.branded.mp4`, 12.000s input to 4.633s output.
- Runnable premise: the same clip with a `spans: []` timeline produced an
  identical 4.633s output, so the spinner backstop alone carries a recording
  whose timeline declares no spans.
- Runnable premise: `brew info vhs` reports 0.12.0 bottled, requiring
  `ffmpeg` and `ttyd`; `ffmpeg` and `ffprobe` are already present and `vhs`
  is not.
- Runnable premise: `drive.py doctor` exits 0 today, reporting `uv`, the
  Playwright browser, `ffmpeg`, and `ffprobe`.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Skill name and trigger handover: settled by the user, Q1.
- Terminal path's home and the `vhs` doctor posture: settled by the user, Q2.
- Timeline contract (`holds` and `leadingCut` only): settled by the
  backstop-only runnable premise above.
