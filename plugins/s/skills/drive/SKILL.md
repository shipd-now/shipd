---
name: drive
description: >-
  Drive a real browser with Playwright to operate an app, verify a change
  against it, and optionally record a branded demo video: resolve the target
  and its credentials, run the `drive.py doctor` preflight, obtain or reuse a
  cached login, start the one-browser session daemon, probe the live DOM
  before authoring any selector, drive the requested instructions while
  waiting for a named completion signal, and end on a PASS/FAIL verdict
  backed by console and network evidence. Use when asked to drive the app,
  verify a change in a real browser, click through a flow, or record a demo
  video of a change. Trigger phrases: "drive the app", "verify this in the
  browser", "click through this flow", "record a demo", "/s:drive".
---

# /s:drive — drive a real browser, verify, and record

You are the **browser-driving layer over a running app**. shipd plans,
builds, reviews, and ships a change, but nothing else in the plugin opens the
app and confirms the change works — the loop otherwise ends at tests and a
pull request. Your job is to close that gap: open a real browser against a
resolved target, drive it through the requested instructions, and end on a
verdict grounded in console and network evidence a reviewer can trust. Where
the request also asks for a demo, you additionally record and post-process a
branded video of the same run.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `s:drive
v<version>` in your first user-visible status sentence (e.g. "s:drive v0.6.207
— resolving the target"), so the user can always see which plugin snapshot the
session is running.

**No `AskUserQuestion`, anywhere in this skill.** Every decision point in this
flow ends its turn as plain text — a numbered list and a typed reply — never a
dialog. This keeps `/s:drive` outside the nine-file `AskUserQuestion` roster
`verified/shipd-interaction` (`dialog-prose-separation`) enumerates: no delta
on that capability is needed because this skill never issues one.

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):
- Control CLI: `${CLAUDE_PLUGIN_ROOT}/skills/drive/scripts/drive.py`
  (`doctor`, `targets`, `login`, `session`, the driving verbs, `probe`,
  `record`, `post`) — stdlib-only, the only script this skill invokes
  directly.
- Recording reference: `${CLAUDE_PLUGIN_ROOT}/skills/drive/references/recording.md`
  (the action-module contract and helper API, read before writing a `record`
  action module).
- Targets example: `${CLAUDE_PLUGIN_ROOT}/skills/drive/references/targets.example.json`
  (the three auth recipe kinds).

## The ordered flow

Run these stages in order. Do not skip a stage or reorder it — each one
supplies evidence or state the next stage depends on.

1. **Resolve the target.** Run `drive.py targets` to print every target
   `drive.py` resolves from `~/.shipd/drive/targets.json`, overridden
   entry-by-entry by `<content-dir>/drive/targets.json` when the repository
   ships one. If the request names a target, use it. **If the request names
   no target and more than one resolves, end this turn as plain text**: a
   numbered list of the resolved target names (and their URLs) and a typed
   reply requesting the choice — never an `AskUserQuestion`. If exactly one
   target resolves, use it without asking.
2. **Preflight.** Run `drive.py doctor`. It exits non-zero only when a tool
   every verb needs (`uv`, the Playwright browser binary) is missing;
   `ffmpeg`/`ffprobe` are reported but do not fail the check unless the
   request needs `record` or `post`. **If a required tool is missing, report
   it and stop** — offer `drive.py doctor --fix` as the next step rather than
   attempting the pipeline against a toolchain `doctor` has already flagged.
3. **Login.** Run `drive.py login <target>`. A cached storage-state file
   inside its TTL is reused with no network login; an expired or missing one
   triggers a fresh login through the browser worker. A failed login reports
   its debug screenshot path — read it before retrying, never guess at what
   went wrong.
4. **Session.** Run `drive.py session start <target>`. This spawns the
   one-browser session daemon that the rest of the run drives — every
   navigation, click, and read happens against this single browser and page,
   so console and network evidence accumulates for the life of the run.
   Starting a session for a different target replaces the running one.
5. **Drive.** Send the requested instructions to the session through the
   driving verbs (`open`, `snapshot`, `click`, `type`, `press`, `wait`,
   `eval`, `shot`). **Probe before you select.** Before authoring any precise
   selector, sample the live DOM with the read-only `drive.py probe` verb
   rather than guessing one from memory or from the app's source — a probe
   dump (accessibility tree, `data-testid`/`data-anchor` inventory, scoped
   HTML, screenshot) is ground truth the running page actually renders; a
   guessed selector is not. **Wait for a named completion signal, never a
   fixed sleep**, before treating any step as finished — a toast appearing, a
   URL changing, an element becoming visible, a network response landing. A
   fixed `sleep` is flaky by construction: too short and it races the app,
   too long and it wastes the run; `drive.py wait` blocks on the signal
   itself.
6. **Verdict.** Unless the request asks for a recording with no checking, end
   the run on a `PASS` or `FAIL` verdict (below). Report it plainly, with its
   evidence, as the closing line of the turn.

Where the request also asks for a demo, run `drive.py record <target>
<action-module>` after step 4 (recording runs its own authenticated session,
independent of the interactive one from step 4) and `drive.py post
<recording>` to assemble the branded, fast-forwarded output — see
`references/recording.md` for the action-module contract before writing one.

## The verdict contract

A drive run's outcome is never asserted from impression — it is computed from
accumulated evidence:

- **Baseline first.** The console errors present immediately after the first
  navigation are the baseline. An error already present there and still
  present afterward does **not** fail the run — it is pre-existing noise, not
  a regression the run introduced.
- **Warnings never fail.** Only errors are evaluated against the baseline;
  a console warning never fails a run regardless of when it appears.
- **Server errors always fail.** Any 4xx or 5xx response to the target's own
  origin fails the run, and the evidence names the specific request.
- **A missing completion signal is a failure, never a `PASS`.** If the named
  completion signal you waited for in step 5 never appears within its
  timeout, the verdict is `FAIL` and states plainly that the signal was never
  observed — the run must reach its real completion signal before any verdict
  is printed. Do not paper over a timeout with a `PASS` because the rest of
  the run looked fine.
- **Report evidence, not adjectives.** State `PASS` or `FAIL` and list the
  console/network lines the verdict rests on — a reviewer reading the report
  should see exactly what happened, not a summary they have to trust.

## Session hygiene

The session daemon is long-lived by design (so console and network evidence
survives navigation), which means it can outlive the turn that started it.
Stop it when the run is done: `drive.py session stop`. If a later `session
start` reports a stale socket, it reclaims it automatically — you do not need
to clean one up by hand, but do not rely on that as a substitute for stopping
your own session when you are finished.
