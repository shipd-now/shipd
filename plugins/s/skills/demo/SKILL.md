---
name: demo
description: >-
  Produce a branded demo video of a change, routing to the right capture
  backend for the subject: a browser app through the drive CLI's `record`
  verb, a command-line tool through its `tape` verb, both converging on the
  same `post` branding stage. Preflights the medium's own toolchain before
  capturing and stops on a missing tool rather than attempting a doomed
  recording. Use when asked to record a demo, make a demo video, or produce
  a branded recording of either a web app or a CLI. Trigger phrases: "record
  a demo", "make a demo video", "/s:demo".
---

# /s:demo — produce a branded demo, browser or terminal

You are the **routing layer over shipd's two capture backends**. A demo video
always ends the same way — the shipd title card, fast-forward treatment, and
badge `post` applies — but it starts differently depending on what is being
demonstrated: a browser app is captured by driving a real browser
(`drive.py record`), a command-line tool by running an annotated terminal
session through `vhs` (`drive.py tape`). Your job is choosing which capture
path the request needs, preflighting only what that path requires, and
handing off to the drive CLI for the capture itself — you never drive a
browser, resolve a target, write selectors, or author a tape directly.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `s:demo
v<version>` in your first user-visible status sentence (e.g. "s:demo v0.6.208
— choosing the capture medium"), so the user can always see which plugin
snapshot the session is running.

**No `AskUserQuestion`, anywhere in this skill.** Every decision point ends
its turn as plain text — a numbered list and a typed reply — never a dialog,
matching `/s:drive`'s own dialog-free contract.

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):
- Control CLI: `${CLAUDE_PLUGIN_ROOT}/skills/drive/scripts/drive.py` —
  `doctor`, `targets`, `login`, `record` (browser capture), `tape` (terminal
  capture), `post` (shared branding). This skill never invokes any other
  script directly.
- Recording reference: `${CLAUDE_PLUGIN_ROOT}/skills/drive/references/recording.md`
  — the browser action-module contract, and the tape annotation contract
  (`#hold`, `#endhold`, `#ready`) for a terminal recording.

## The ordered flow

1. **Choose the medium.** Read the request for what is being demonstrated. A
   web application, a UI, or a target already configured in
   `drive.py targets` is a **browser** demo. A CLI, a terminal workflow, or a
   command being run is a **terminal** demo. **If the request names no medium
   and the subject could reasonably be either, end this turn as plain text**:
   a numbered list of the two mediums and a typed reply requesting the
   choice — never an `AskUserQuestion`. If the subject is unambiguous, choose
   without asking.
2. **Preflight only what the chosen medium needs.** Run `drive.py doctor`.
   For a browser demo, a missing `uv`, Playwright browser binary, `ffmpeg`,
   or `ffprobe` blocks capture. For a terminal demo, a missing `uv` or `vhs`
   blocks capture (the Playwright browser binary is not needed for `tape`,
   but `doctor` still reports it). **If the tool the chosen medium needs is
   missing, report `doctor`'s remedy for it and stop** — never attempt the
   capture against a toolchain `doctor` already flagged. A terminal demo
   never fails on a missing `ffmpeg`/`ffprobe` alone, and a browser demo
   never fails on a missing `vhs` alone — each medium is blocked only by its
   own tier.
3. **Capture.**
   - **Browser subject:** follow `/s:drive`'s own target-resolution and login
     steps (`drive.py targets`, `drive.py login <target>`) to obtain a
     session with cached auth, then run
     `drive.py record <target> <action-module>`. Probe the live DOM with
     `drive.py probe` before writing any selector into the action module —
     never guess one from memory or from the app's source. See
     `references/recording.md`'s action-module contract before writing one.
   - **Terminal subject:** author (or use the supplied) `vhs` tape file,
     annotated with `#hold`/`#endhold` around any stretch that must stay at
     normal speed and `#ready` marking the point the shell prompt has
     settled — see `references/recording.md`'s tape section for the worked
     example. Run `drive.py tape <tape-file>` unmodified; do not pass any
     flag that would change what the tape itself declares.
4. **Post-process.** Run `drive.py post <recording>` (the timeline path
   defaults to beside the recording; `record` and `tape` both write one in
   that shape) to cut the leading boot, fast-forward eligible dead air, and
   composite the title card and badge. This stage is identical for both
   mediums — neither capture path changes what `post` does.
5. **Report.** State the medium chosen and why, then the branded output path
   `post` printed (and the GIF path too, if `--gif` was requested).

## Trigger handover

This skill owns `record a demo`, surrendered by `/s:drive`'s own trigger
phrases — exactly one skill answers to it. `/s:drive` still exposes `record`
and `post` as CLI verbs this skill drives, and keeps its own browser
verification triggers (`drive the app`, `verify this in the browser`, `click
through this flow`) unrelated to producing a video.
