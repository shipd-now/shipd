<!-- description: Produce a branded demo video, routing a browser subject to `record` and a terminal subject to `tape`, both converging on `post`. -->
# /s:demo — produce a branded demo, browser or terminal

Choose the capture backend a demo needs — a browser app through the drive
CLI's `record` verb, a command-line tool through its `tape` verb — and hand
off to it. Both converge on the same `post` branding stage, so every demo
carries the same title card, fast-forward treatment, and badge whatever
captured it. Never drive a browser, resolve a target, or author a tape
directly; delegate capture to the drive CLI and own only the routing, the
medium choice, and the report.

**Announce the version first.** Read the plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and open with `s:demo
v<version>` in your first status sentence.

**No dialog, ever.** Every decision point ends its turn as plain text — a
numbered list and a typed reply — never an interactive question tool.

`D="${CLAUDE_PLUGIN_ROOT}/skills/drive/scripts/drive.py"` — the stdlib-only
control CLI; the only script this command invokes directly. Everything below
runs as `python3 "$D" <verb> ...`.

## 1. Choose the medium

Read the request for what is being demonstrated: a web application or a
configured target is a **browser** demo, a CLI or terminal workflow is a
**terminal** demo. **No medium named and the subject could be either** → end
the turn as plain text: a numbered list of the two mediums, then read the
typed reply — never a dialog. An unambiguous subject needs no asking.

## 2. Preflight only what the medium needs

Run `doctor`. A browser demo is blocked by a missing `uv`, Playwright browser
binary, `ffmpeg`, or `ffprobe`; a terminal demo is blocked by a missing `uv`
or `vhs` only — never by the other medium's tools. A blocked tool stops the
flow here: report `doctor`'s remedy for it rather than attempting the
capture.

## 3. Capture

- **Browser subject:** resolve the target (`targets`), log in
  (`login <target>`), then run `record <target> <action-module>`. Probe the
  live DOM (`probe`) before authoring any selector — see
  `${CLAUDE_PLUGIN_ROOT}/skills/drive/references/recording.md`'s
  action-module contract before writing one.
- **Terminal subject:** author (or use the supplied) `vhs` tape file,
  annotated with `#hold`/`#endhold` around any stretch that must stay at
  normal speed and `#ready` marking the settled prompt — see
  `references/recording.md`'s tape section for the worked example. Run
  `tape <tape-file>` unmodified.

## 4. Post-process

Run `post <recording>` — identical for both mediums, cutting the leading
boot, fast-forwarding eligible dead air, and compositing the title card and
badge.

## 5. Report

State the medium chosen and why, then the branded output path `post`
printed (and the GIF path too, if `--gif` was requested).
