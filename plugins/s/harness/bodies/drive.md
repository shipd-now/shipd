<!-- description: Drive a real browser with Playwright to operate an app, verify a change against it, and record a branded demo video. -->
# /s:drive — drive a real browser, verify, and record

Open a real browser against a resolved target, drive it through the requested
instructions, and end on a `PASS`/`FAIL` verdict grounded in console and
network evidence. Optionally record and post-process a branded demo of the
same run. Nothing here touches the spec engine — this command drives an app,
not `.shipd/`.

**Announce the version first.** Read the plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and open with `s:drive
v<version>` in your first status sentence.

**No dialog, ever.** Every decision point ends its turn as plain text — a
numbered list and a typed reply — never an interactive question tool.

`D="${CLAUDE_PLUGIN_ROOT}/skills/drive/scripts/drive.py"` — the stdlib-only
control CLI; the only script this command invokes directly. Everything below
runs as `python3 "$D" <verb> ...`.

## 1. Resolve the target

Run `targets` to list what resolves from `~/.shipd/drive/targets.json`,
overridden entry-by-entry by `<content-dir>/drive/targets.json`. A named
target in the request wins outright. **No target named and more than one
resolves** → end the turn as plain text: a numbered list of names and URLs,
then read the typed reply — never a dialog. Exactly one resolves → use it.

## 2. Preflight

Run `doctor`. It fails only when a tool every verb needs (`uv`, the
Playwright browser binary) is missing; `ffmpeg`/`ffprobe` are reported but
only block `record`/`post`. A required-tool failure stops the flow here —
offer `doctor --fix` rather than pushing on against a flagged toolchain.

## 3. Login

Run `login <target>`. A cached storage-state file inside its TTL is reused
with no network call; an expired or missing one triggers a real login. A
failure names a debug screenshot path — read it before retrying.

## 4. Start the session

Run `session start <target>`. One browser, one page, for the life of the run
— console and network evidence accumulates across every navigation this
session makes. Starting a session for a different target replaces the
running one.

## 5. Drive the instructions

Send the requested steps through the driving verbs: `open`, `snapshot`,
`click`, `type`, `press`, `wait`, `eval`, `shot`.

- **Probe before you select.** Run the read-only `probe` verb against the
  live page before authoring any precise selector — its accessibility tree,
  `data-testid`/`data-anchor` inventory, scoped HTML, and screenshot are
  ground truth; a selector guessed from memory or source is not.
- **Wait for a named completion signal, never a fixed sleep.** `wait` blocks
  on the signal itself — a URL change, an element becoming visible, a
  network response landing — before any step counts as finished.

## 6. Verdict

Unless the request wants a recording with no checking, close on `PASS` or
`FAIL`, computed — never impression-based:

- The console errors present right after the first navigation are the
  **baseline**; an error already there and still there afterward does not
  fail the run.
- Warnings never fail a run.
- Any 4xx/5xx response to the target's own origin fails the run, naming the
  request.
- A completion signal that never appears within its timeout is `FAIL`,
  stating plainly it was never observed — never `PASS` on a timeout.

Report the verdict with the evidence lines it rests on, not a summary.

## 7. Recording (only when the request asks for a demo)

After step 4, run `record <target> <action-module>` — see
`${CLAUDE_PLUGIN_ROOT}/skills/drive/references/recording.md` for the
action-module contract and helper API before writing one — then `post
<recording>` to assemble the branded, fast-forwarded output.

## Session hygiene

The session daemon outlives the turn that started it by design. Stop it when
the run is done: `session stop`. A later `session start` reclaims a stale
socket automatically, but do not rely on that instead of stopping your own.
