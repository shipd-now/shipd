<!-- doc-type: how-to -->

# Drive a browser and record a demo

`/s:drive` opens a real browser against a running app, drives it through your
instructions, and ends on a `PASS` or `FAIL` verdict. The verdict rests on
console and network evidence, not on impression. `/s:demo` produces a branded
demo video of a browser app or a terminal session. Both skills run the same
control CLI, `drive.py`, which drives the browser through Playwright.

## When to use it

- **Verify a change in the app.** Run `/s:drive` after a build, when tests
  pass but nobody has opened the app.
- **Click through a flow.** Run `/s:drive` to operate a page and collect what
  the console and the network reported.
- **Show a change.** Run `/s:demo` for a video of a browser app or a
  command-line tool.

## How to run it

### Drive and verify

1. Run `/s:drive` with a target and the instructions:

   ```
   /s:drive on staging, create a project and confirm the toast appears
   ```

2. Answer any typed question the skill asks. Neither skill opens a dialog.

The skill then runs these stages in order:

1. **Resolve the target.** `drive.py targets` prints each target from
   `~/.shipd/drive/targets.json`. A repository's
   `<content-dir>/drive/targets.json` overrides it entry by entry. With
   several targets and none named, the skill asks you to choose one.
2. **Preflight.** `drive.py doctor` exits non-zero when `uv` or the
   Playwright browser binary is missing. The skill then stops and offers
   `drive.py doctor --fix`.
3. **Log in.** `drive.py login <target>` reuses a cached login inside its
   TTL, or logs in afresh. A target with auth kind `none` needs no login.
4. **Start the session.** `drive.py session start <target>` starts one
   headless browser that the rest of the run drives. Add `--headed` to watch
   it.
5. **Drive.** The skill sends the driving verbs to the session. It probes
   the live page with `drive.py probe` before it writes any selector. It
   waits on a named completion signal with `drive.py wait`, never a fixed
   sleep.
6. **Report the verdict.** The skill ends on `PASS` or `FAIL`, with the
   console and network lines it rests on.

### Log in by hand

A failed login reports a debug screenshot path. For MFA, SSO, a passkey, or
an OAuth consent screen, log in yourself:

```
drive.py login <target> --manual
```

The verb opens a visible Chromium window at the login page and waits while
you log in. The window may open behind the terminal. The verb writes the same
cached login the session loads, and also replaces a stale cached login.

### Take over a stuck step

When a driving verb fails or a `wait` times out, the skill offers a handoff:

1. Run `drive.py handoff <signal>`, naming the signal that failed to appear.
2. Take the step by hand in the visible browser.
3. Run `drive.py resume` to give the session back.

The handoff relaunches the browser visible, and keeps the login, the URL, and
the recorded events. It opens a new page, so it loses unsaved page state,
such as text typed into a form. Your own clicks during the handoff never fail
the verdict.

### Record a demo

1. Run `/s:demo` with the subject:

   ```
   /s:demo the project creation flow on staging
   ```

2. Choose the medium when the skill asks: browser or terminal.

The skill captures the subject in one of two ways:

- **Browser subject.** The skill logs in as `/s:drive` does, then runs
  `drive.py record <target> <action-module>`. It probes the page before it
  writes a selector into the action module.
- **Terminal subject.** The skill runs `drive.py tape <tape-file>` on an
  annotated `vhs` tape. `#hold` and `#endhold` mark a stretch that keeps
  normal speed, and `#ready` marks the settled prompt.

Both mediums end with `drive.py post <recording>`. It cuts the leading boot,
fast-forwards dead air, and adds the title card and badge. The skill reports
the branded output path. `doctor` blocks a browser demo only on a missing
`uv`, Playwright browser, `ffmpeg`, or `ffprobe`. It blocks a terminal demo
only on a missing `uv` or `vhs`.

## Reference

### The verdict

| Evidence | Effect |
| --- | --- |
| A console error present right after the first navigation | Baseline; it never fails the run. |
| A new console error | Fails the run. |
| A console warning | Never fails the run. |
| A 4xx or 5xx response from the target's own origin | Fails the run, naming the request. |
| A completion signal that never appears | Fails the run. |
| Errors inside a handoff window | Listed under `during handoff`; never fail the run. |

### `drive.py` verbs

| Verb | Effect |
| --- | --- |
| `doctor` | Reports prerequisite state; `--fix` installs what it can. |
| `targets` | Prints each resolved target's name, URL, and auth kind. |
| `login` | Obtains or reuses a cached login; `--manual` logs in by hand. |
| `session` | Starts, checks, or stops the browser session daemon. |
| `open` | Navigates the session's page. |
| `snapshot` | Prints an accessibility-tree snapshot of the current page. |
| `click`, `type`, `press` | Click an element, type text into it, or press a key. |
| `wait` | Waits for a named completion signal. |
| `eval` | Evaluates a JavaScript expression on the page. |
| `shot` | Takes a screenshot. |
| `handoff` | Relaunches the browser visible and hands it to you. |
| `resume` | Takes the session back and closes the handoff window. |
| `console`, `network` | Print the console or response events since the session started. |
| `probe` | Samples the page read-only: tree, test ids, scoped HTML, screenshot. |
| `record` | Records a browser demo by running an action module. |
| `tape` | Records a terminal session from a `vhs` tape file. |
| `post` | Turns a recording into a branded, fast-forwarded video. |

Stop the session when the run ends: `drive.py session stop`.

### Related pages

- [Build a change](build.md) — the build a drive run verifies.
