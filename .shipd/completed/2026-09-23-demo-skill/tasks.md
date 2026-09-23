## 1. The vhs doctor tier

- [x] 1.1 [req: drive-doctor] Add tests to
      `plugins/s/skills/drive/tests/test_drive_cli.py` covering the new tier:
      `doctor` reports `vhs` with a `brew install vhs` remedy; an absent
      `vhs` with `uv` and the browser present still exits 0; `doctor --fix`
      attempts no `vhs` install and still names the manual remedy. Use the
      existing presence-reporting seams rather than touching the host
      toolchain. Run them and observe them fail.
- [x] 1.2 [req: drive-doctor] Extend `doctor_report()` and its remedy table
      in `plugins/s/skills/drive/scripts/drive.py` with a `vhs` row marked
      terminal-recording-only, mirroring how `ffmpeg`/`ffprobe` are marked
      recording-only. Leave `cmd_doctor`'s `--fix` path untouched so it still
      installs only the Playwright browser binary. Run task 1.1's tests until
      they pass.

## 2. Tape recording

- [x] 2.1 [req: drive-tape-timeline] Add a
      `plugins/s/skills/drive/tests/test_drive_tape.py` with a
      `TapeAnnotationTests` case for the pure annotation reader: `#hold` and
      `#endhold` become one `holds` window; an unclosed `#hold` extends to the
      recording end; `#ready` becomes `leadingCut`; a tape with no annotations
      yields empty `holds` and no `leadingCut`; `Sleep` directives contribute
      no `spans`. Run it and observe it fail.
- [x] 2.2 [req: drive-tape-timeline] Create
      `plugins/s/skills/drive/scripts/tape.py` holding the pure layer only: a
      `read_annotations(tape_text)` returning the `holds`/`leadingCut`
      timeline, with offsets accumulated from the tape's own directive
      ordering. Stdlib only, no subprocess. Run task 2.1's tests until they
      pass.
- [x] 2.3 [req: drive-tape] Add a `TapeVerbTests` case to
      `test_drive_tape.py` driving `drive.py tape` with an injected runner:
      a successful run writes a video and a timeline beside each other and
      prints one JSON object carrying both paths; a non-zero `vhs` exit
      reports the failure, writes no timeline, and exits non-zero; an absent
      `vhs` names `brew install vhs`, records nothing, and exits non-zero.
      Follow the injectable-runner pattern `cmd_doctor` already uses
      (`default_run`). Run it and observe it fail.
- [x] 2.4 [req: drive-tape] Implement `cmd_tape(args, run=default_run)` in
      `drive.py`: resolve `vhs` on PATH and refuse with the remedy when
      absent; invoke `vhs` on the tape through the injectable runner; on a
      non-zero exit report and stop without writing a timeline; on success
      write the timeline from `tape.read_annotations` beside the recording and
      print the `{"video": ..., "timeline": ...}` object matching `record`'s
      shape. Start no browser, resolve no target, and perform no login. Wire
      its subparser. Run task 2.3's tests until they pass.
- [x] 2.5 [req: drive-tape] Add an end-to-end test asserting a tape
      recording's timeline is accepted by `post` unchanged — feed
      `cmd_post`'s timeline loader a `read_annotations` result and assert it
      parses and drives `compute_ff_spans` without a `spans` key error. This
      is the seam that keeps the two media converging.

## 3. The demo skill

- [x] 3.1 [req: demo-skill-flow] Write
      `plugins/s/skills/demo/SKILL.md` with frontmatter `name: demo` and a
      description whose trigger phrases include `record a demo`, `make a demo
      video`, and `/s:demo`. Body: announce the plugin version first; run the
      drive CLI's `doctor` before capturing and stop on a missing tool for the
      chosen medium; route a browser subject to `record` and a terminal
      subject to `tape`; post-process both through `post`; end an ambiguous
      medium as a plain-text numbered list, never an interactive question
      tool. Match `plugins/s/skills/drive/SKILL.md`'s structure and its
      dialog-free contract.
- [x] 3.2 [req: demo-skill-registration] Write
      `plugins/s/harness/bodies/demo.md` mirroring the skill, following
      `plugins/s/harness/bodies/drive.md`'s shape — the leading
      `<!-- description: ... -->` comment, the version-announcement rule, and
      the `${CLAUDE_PLUGIN_ROOT}` script path convention.
- [x] 3.3 [req: demo-skill-registration] Remove `record a demo` from the
      trigger phrases in `plugins/s/skills/drive/SKILL.md`'s frontmatter
      description and from `plugins/s/harness/bodies/drive.md`'s description
      comment, leaving drive's browser-verification triggers intact.
- [x] 3.4 [req: demo-skill-registration] Add a test to
      `plugins/s/skills/build/tests/test_harness_bodies.py` asserting exactly
      one skill declares the `record a demo` trigger phrase, so the two skills
      can never both claim it. Confirm the existing skills-to-bodies 1:1 guard
      passes with the new pair.

## 4. Reference and verification

- [x] 4.1 [req: drive-tape-timeline] Add a tape section to
      `plugins/s/skills/drive/references/recording.md` documenting the
      annotation comments (`#hold`, `#endhold`, `#ready`), stating that dead
      air is left to the backstop and that no spans are derived from `Sleep`,
      and showing one worked tape. Keep it beside the action-module contract
      so both media's authoring rules sit in one reference.
- [x] 4.2 [req: demo-skill-flow] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` to the next patch version, as the
      cache-snapshot rule in `AGENTS.md` requires for any change touching
      `plugins/s/`.
- [x] 4.3 [req: demo-skill-flow] Run
      `python3 -m unittest discover -s plugins/s/skills/drive/tests` and
      `python3 -m unittest discover -s plugins/s/skills/build/tests`, and fix
      anything that fails until both are clean.
