# /s:video-ingest — the brief grammar and its install rules

The long form the router points at. Read it before composing; the engine's
linter enforces every piece of the skeleton below at install time and removes
anything it installed on a finding.

## The skeleton

```
# <brief title>
Video: <source recording's name, from the bundle manifest's `source` field>
Bundle: <bundle slug>
Project: <declared workspace-registry project slug, when the project is known>

## Intents

### <intent title>

Prose describing the requested change, citing the frame and transcript
evidence it rests on [1].

### <intent title>

...

## Open questions

- Conflicting statements that recency cannot order — each position with its
  timestamp, neither recorded as the outcome.

## Sources

1. [HH:MM:SS] <what they said>
2. [HH:MM:SS] <what they said>
```

## The rules the linter enforces

- **Title.** Line 1 is a non-empty `# <title>`.
- **Header metadata.** The contiguous `Key: value` lines *immediately* after
  the title — the block ends at the first blank line or heading — must include
  a `Video:` line. **No blank line between the title and the first metadata
  line**: one blank line there yields zero metadata and a missing-`Video:`
  finding.
- **`Video:` is the recording, `Bundle:` is the bundle — different values.**
  `Video:` carries the source recording's name, read from the working bundle's
  manifest `source` field (a basename is fine). `Bundle:` carries the ingest
  directory's own slug. Putting the bundle slug in `Video:` loses the
  provenance link back to the recording that was actually ingested.
- **`Project:` is authored only when the project is known**, never guessed —
  named at invocation, or resolvable because the invoking repository is a
  declared project in the workspace registry. Otherwise omit the line
  entirely; the brief still installs clean without it.
- **Intents.** A `## Intents` section carrying at least one `### ` heading,
  each with at least one inline `[n]` citation marker resolving to a listed
  source.
- **Sources.** A `## Sources` section with at least one numbered entry whose
  text **opens with a bracketed timestamp** — `[HH:MM:SS]`, zero-padded,
  fractional seconds permitted — followed by what was said. No speaker is
  named anywhere.
- **Citations.** Every `[n]` marker outside a fenced code block must reference
  a listed source number. A `[n](` link is not a citation marker.
- **Optional sections.** `## Open questions` and `## Gaps & caveats` are
  optional; any other unrecognized level-2 section is permitted, not an error.

**Zero-pad every source timestamp.** Transcript offsets are raw seconds, and
the grammar wants a three-field `[HH:MM:SS]`, so format explicitly: `312.4`
seconds is `[00:05:12]`, never `[5:12]` and never `[0:05:12]`. A naively
formatted sub-hour timestamp fails the install.

## Install mechanics

Author into a staging file at any working path **outside** the content
directory, then install it through the emit engine. Never write into the tree
directly and never construct a `video/` path in either direction — you name
the slug, the engine owns the path.

- **The slug** is kebab-case and independent of the bundle's slug, though
  reusing it is reasonable. The brief lands at `video/<slug>/brief.md` under
  the resolved content directory.
- **Validate then install.** The engine copies the staged brief into place,
  runs the checks in process, and on any finding removes what it installed and
  exits non-zero — an invalid brief never lands. Fix the staged file and
  re-run until it exits 0; never finish on a non-zero install.
- **Replace.** Re-running against an existing brief is refused unless
  `--replace` is passed. Use it only when overwriting is the intent.
- **Read back through the engine**, never by opening the installed path.

## The pointer crop

A cited frame's entry may carry a `cursor` object naming a zoom-crop file
beside the full frame's own. A roughly 20-pixel cursor is effectively
invisible in the full frame and unmistakable in the crop, so read the crop and
name the element under the pointer as the intent's target — it is the
strongest available evidence of what was being discussed. Where the `cursor`
object's `origin` is `carried`, the recorded position is the pointer's last
known **resting place**, not a gesture made as those words were spoken.

## The inversion trap

A speaker says "these filters are sensor aligned which is kind of weird" while
the grounded frame shows the option list already centre-aligned (the speech
recognition mishearing "center" as "sensor" is a separate issue — the frame
outranks the transcript). Reading only the adjective and the frame's layout,
it is tempting to write:

- **Wrong:** "### Center-align the option list" — this instructs a planner to
  apply the exact layout the speaker was complaining about, reproducing the
  complaint rather than resolving it.
- **Right:** "### Left-align the option list", or whatever non-centred layout
  the surrounding evidence supports — the change *away* from the disapproved
  state.
