## 1. Author the skill

- [x] 1.1 [req: video-skill-pipeline] Create
      `plugins/s/skills/video-ingest/SKILL.md` with the YAML frontmatter
      (`name: video-ingest`, a `description` naming what it does and its trigger
      phrases including "/s:video-ingest", matching the shape of
      `plugins/s/skills/research/SKILL.md`), the role statement, and a
      **version announcement** instruction mirroring `/s:research`.
- [x] 1.2 [req: video-skill-pipeline] In that `SKILL.md`, write the staged
      pipeline section: run `video_ingest.py doctor` and stop on a missing
      required tool; obtain the bundle by ingesting a supplied video path or
      reusing a supplied slug via `video_ingest.py path <slug>`; read
      `transcript.json` and `frames.json`; and stop without installing when no
      actionable intent is found. Name the script by its
      `${CLAUDE_PLUGIN_ROOT}/skills/video-ingest/scripts/video_ingest.py` path.
- [x] 1.3 [req: video-skill-frame-grounding] In that `SKILL.md`, write the
      grounding section: anchor each intent on the `start` of the words
      expressing it (never the enclosing segment, which splits only at speaker
      changes and can span tens of seconds), resolve the nearest `frames.json`
      entry, read only those frames, and prefer what a frame shows over the
      transcript's wording when they disagree — noting the transcript's version
      rather than asserting a misheard term.
- [x] 1.4 [req: video-skill-arbitration] In that `SKILL.md`, write the speakers
      and arbitration section: mine names from self-identification and direct
      address, fall back to the diarization label, apply the decider's latest
      statement and retain superseded statements with speaker and timestamp,
      and record a conflict as an `## Open questions` entry when no decider is
      configured.
- [x] 1.5 [req: video-skill-brief-emission] In that `SKILL.md`, write the brief
      grammar and emission section: reproduce the shipped grammar from
      `.shipd/README.md`'s "Video intent briefs", require zero-padded `HH:MM:SS`
      source timestamps, and specify staging plus
      `spec_emit.py video <slug> --from <file>` with a fix-and-re-run loop until
      the install exits zero. State that the skill never writes into the content
      directory's `video/` folder directly.
- [x] 1.6 [req: video-skill-pipeline] In that `SKILL.md`, write the ending
      section: report the installed brief's slug and location, summarize the
      extracted intents, and stop without planning or building anything.

## 2. Verify against the real recording

- [x] 2.1 [req: *] Verify the frontmatter is loadable: read
      `plugins/s/skills/video-ingest/SKILL.md` back and confirm it opens with a
      `---` block carrying `name` and `description`, matching the shape of
      `plugins/s/skills/research/SKILL.md`. Do not run `claude plugin update`
      — the snapshot refresh belongs to the post-merge close-out, not this
      branch.
- [x] 2.2 [req: *] Dry-run the pipeline's mechanics by hand against the existing
      bundle at `~/.shipd/video/video-ingest-frames-verify` (do not re-ingest):
      read its `transcript.json` and `frames.json`, pick the word anchors for
      each candidate intent, resolve the nearest frame for each, and read those
      frames. Record which frames each intent resolved to.
- [x] 2.3 [req: *] Compose a brief from 2.2 following the SKILL.md instructions
      and install it with `spec_emit.py video <slug> --from <file>` into a
      scratch content directory (use `--root` pointing at a temp dir outside the
      repo, so nothing lands in the worktree). Fix and re-run until it exits
      zero, and record how many attempts the install took.
- [x] 2.4 [req: *] Compare the composed brief's intents against the four changes
      actually requested in the reference recording — button styling, filter
      alignment, `add filter` capitalisation, and header consistency. Record in
      the PR description which were captured, which were missed, and any intent
      that was invented. Also record whether the brief propagated the
      transcript's `sensor aligned` or corrected it from the frame.

## 3. Ship

- [x] 3.1 [req: *] Confirm the repo is clean of verification artifacts: the
      scratch brief from 2.3 lives outside the worktree and `git status` shows
      only the intended `SKILL.md` and `plugin.json` changes.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/video-ingest/tests` and `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm both pass — this member changes
      no engine code, so both suites must be unchanged and green.
- [x] 3.3 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.79` to `0.6.80`.
