## 1. Control CLI skeleton and preflight

- [x] 1.1 [P1] [req: drive-doctor] Under `plugins/s/skills/drive/tests/`, add `test_drive_cli.py` and `_stubs.py`, copying the PATH-stubbing helper shape from `plugins/s/skills/video-ingest/tests/_stubs.py`. Cover: an unknown verb prints usage on stderr and exits 2; `doctor` with `uv` stubbed away exits non-zero naming a remedy; `doctor` with `uv` and the browser present but `ffmpeg` absent exits 0 and marks `ffmpeg` recording-only. Run it and observe it fail — the CLI does not exist yet.
- [x] 1.2 [P2] [req: drive-doctor] Under `plugins/s/skills/drive/scripts/`, create `drive.py` as a stdlib-only Python 3 CLI with an argparse verb table (`doctor`, `targets`, `login`, `session`, `open`, `snapshot`, `click`, `type`, `press`, `wait`, `eval`, `shot`, `console`, `network`, `probe`, `record`, `post`), a fatal-error helper printing one `Error: <reason>` line on stderr with a non-zero exit, and usage on stderr with exit 2 for an unknown or missing verb.
- [x] 1.3 [P3] [req: drive-doctor] In that `drive.py`, implement `doctor`: a tool table of `uv` and the Playwright browser binary as always-required and `ffmpeg`/`ffprobe` as recording-only, each with a remedy hint, resolved through an injectable runner so the tests never touch the host toolchain. Exit non-zero only when an always-required tool is missing.
- [x] 1.4 [P4] [req: drive-doctor] In that `drive.py`, implement `doctor --fix`: state the network access it will perform, then install the missing browser binary through the Playwright worker and re-report. Confirm the test file from task 1.1 passes.

## 2. Targets, credentials, and the auth cache

- [x] 2.1 [P5] [req: drive-targets-config] Under `plugins/s/skills/drive/tests/`, add `test_drive_targets.py` covering: a repository-level targets entry under the content directory's drive folder overriding the same-named entry in the user-level file; `env` and `command` auth recipes resolving both secrets; the login worker's argv carrying no secret while its environment does; and an unknown target producing one `Error:` line and a non-zero exit. Run it and observe it fail.
- [x] 2.2 [P6] [req: drive-targets-config] In `drive.py`, implement target resolution: read the user-level targets file under `~/.shipd/drive/`, read the repository-level one under the resolved content directory's `drive/` folder, and merge the second over the first entry-by-entry by target name.
- [x] 2.3 [P7] [req: drive-targets-config] In `drive.py`, implement the three auth recipes — `none`, `env` (two variable names), and `command` (two argv arrays whose stdout is the secret, trailing newline stripped) — and pass the resolved secrets to a worker through its environment only, never in argv and never in any printed line.
- [x] 2.4 [P8] [req: drive-targets-config] In `drive.py`, implement the `targets` verb printing each resolved target's name, url, and auth kind, with no secret and no resolved credential value.
- [x] 2.5 [P8] [req: drive-auth-cache] Under `plugins/s/skills/drive/tests/`, add `test_drive_auth_cache.py` covering: an auth file whose modification time is inside the TTL skips the login worker; one older than the TTL runs it; a failed login leaves the previous auth file untouched and exits non-zero. Run it and observe it fail.
- [x] 2.6 [P9] [req: drive-auth-cache] In `drive.py`, implement the `login` verb: resolve `authCacheTtlHours` (default 8), reuse the target's auth file under `~/.shipd/drive/auth/` while its mtime is inside the TTL, otherwise invoke the login worker and overwrite it, and on failure report the debug screenshot path and exit non-zero without touching the previous file. Confirm the test file from task 2.5 passes.

## 3. The Playwright browser worker

- [x] 3.1 [P1] [req: drive-session] Under `plugins/s/skills/drive/scripts/`, create `browser_worker.py` with a PEP 723 inline-dependency header declaring `playwright`, matching the header shape of `plugins/s/skills/video-ingest/scripts/backends/asr_whisper.py`, and a subcommand table of `login`, `session`, `probe`, `cards`, and `install-browser`.
- [x] 3.2 [P2] [req: drive-session] In that `browser_worker.py`, implement `login`: read the username and password from the environment, drive the generic login form (email field, optional continue step, password field, submit), wait until the URL leaves the authentication screen, re-navigate to the requested host when the flow redirected elsewhere, and write the storage state to the requested path. On failure write a debug screenshot beside it and exit non-zero.
- [x] 3.3 [P3] [req: drive-session] In that `browser_worker.py`, implement `session`: launch one browser and one page with the target's storage state, attach `console` and `response` listeners once and append every event to in-memory buffers that survive navigation, then serve newline-delimited JSON requests on a Unix socket under `~/.shipd/drive/`, replying with one JSON object per request.
- [x] 3.4 [P4] [req: drive-session] In that `browser_worker.py`, implement the request handlers the driving verbs need — navigate, accessibility snapshot, click, type, press, wait, evaluate, screenshot, console, network, and close — each returning a JSON reply and reporting a handler failure as a JSON error rather than killing the daemon.
- [x] 3.5 [P5] [req: drive-session] In that `browser_worker.py`, implement `probe` as a read-only sampler: navigate, optionally perform one non-destructive reveal click, then dump the scoped accessibility tree, a `data-testid` and `data-anchor` inventory, truncated scoped HTML, and a screenshot. Perform no submitting, saving, or creating.

## 4. Session verbs and the verdict

- [x] 4.1 [P9] [req: drive-session] Under `plugins/s/skills/drive/tests/`, add `test_drive_session.py` covering, against a fake socket server: a driving verb sending one JSON request and printing the reply; `console` returning events recorded before the verb ran; `session start` for a different target stopping the running daemon first; and `session status` reporting a stale socket. Run it and observe it fail.
- [x] 4.2 [P10] [req: drive-session] In `drive.py`, implement `session start|status|stop`: spawn the browser worker as a background process through `uv run`, record the target and pid in a session state file under `~/.shipd/drive/`, reclaim a stale socket on start, and replace a running session whose target differs.
- [x] 4.3 [P11] [req: drive-session] In `drive.py`, implement the driving verbs as thin socket clients that send one JSON request and print the JSON reply, reporting a connection failure as one `Error:` line with a non-zero exit. Confirm the test file from task 4.1 passes.
- [x] 4.4 [P11] [req: drive-verdict] Under `plugins/s/skills/drive/tests/`, add `test_drive_verdict.py` covering: an error present in the baseline and again afterwards does not fail; a warning never fails; a 500 response to the target's origin fails and the evidence names the request; an unobserved completion signal yields `FAIL` stating the signal was never observed. Run it and observe it fail.
- [x] 4.5 [P12] [req: drive-verdict] In `drive.py`, implement the verdict computation over a baseline console set, a final console set, and the accumulated network log, returning `PASS` or `FAIL` with its evidence lines. Confirm the test file from task 4.4 passes.

## 5. Recording

- [x] 5.1 [P1] [req: drive-recording] Under `plugins/s/skills/drive/scripts/`, create `record_worker.py` with a PEP 723 header declaring `playwright`: record the browser to video with the target's storage state, import the action module by path, and call its `run(page, h, base_url)`.
- [x] 5.2 [P2] [req: drive-recording] In that `record_worker.py`, implement the helper object `h`: injected cursor, glide-and-click, glide-and-type, anchored annotation card, element highlight, protected `hold`, recorded wait, and content-ready mark.
- [x] 5.3 [P3] [req: drive-recording] In that `record_worker.py`, implement the semantic timeline: accumulate `spans` from recorded waits, `holds` from `hold` calls and every annotation's visible window, and `leadingCut` from the content-ready mark, then write them beside the recording as a timeline JSON file and hold a protected tail beat before closing.
- [x] 5.4 [P13] [req: drive-recording] In `drive.py`, implement the `record` verb: resolve the target and its cached auth, invoke the record worker through `uv run`, and print the recording and timeline paths.

## 6. Post-processing and branded frames

- [x] 6.1 [P3] [req: drive-postprocess] Under `plugins/s/skills/drive/tests/`, add `test_drive_postprocess.py` covering the pure span algebra with no ffmpeg invocation: a three-second static stretch is not fast-forwarded; a stretch inside a `holds` window is excluded from fast-forward; the spinner backstop's spans are unioned with the timeline's; the resulting segment list covers the whole body with nothing cut; the leading cut prefers `leadingCut`, then the detected content start, then the fixed fallback. Run it and observe it fail.
- [x] 6.2 [P4] [req: drive-postprocess] Under `plugins/s/skills/drive/scripts/`, create `postprocess.py` as stdlib-only Python 3 implementing the span algebra: merge blocks split by a short blip, drop blocks under the five-second floor, subtract every `holds` window, hold the final result at normal speed, and emit the ordered segment list.
- [x] 6.3 [P5] [req: drive-postprocess] In that `postprocess.py`, implement the spinner backstop: sample the video to a small grayscale grid through ffmpeg, classify a sample as waiting when the frame is near-blank or the union of changed cells across a time window stays small, and group the samples into spans.
- [x] 6.4 [P6] [req: drive-postprocess] In that `postprocess.py`, implement the assembly: cut the leading boot, encode each segment at normal speed or ten times speed, composite the badge over fast-forwarded segments only, prepend the title card, concatenate, and write the output. Confirm the test file from task 6.1 passes.
- [x] 6.5 [P7] [req: drive-postprocess] In that `postprocess.py`, add the inline-embeddable output option writing an animated GIF beside the video.
- [x] 6.6 [P7] [req: drive-brand-frames] Under `plugins/s/skills/drive/tests/`, add `test_drive_brand.py` covering: the title defaults to the slug of a `change/<slug>` branch, falls back to a supplied title otherwise, and is never read from an issue-tracker identifier; the badge geometry for a 1280 by 720 frame is at most 44 by 180 pixels; the badge overlay is applied to fast-forwarded segments only. Run it and observe it fail.
- [x] 6.7 [P8] [req: drive-brand-frames] In `browser_worker.py`, implement `cards`: render the title card with the U+2615 coffee mark as its hero glyph on `#0f172a` under the wordmark gradient `#8888a0` to `#c6ff4e`, and render the fast-forward badge as a flat pill at most 44 pixels tall and 180 pixels wide carrying the speed factor and a single chevron, with no border and no glow.
- [x] 6.8 [P14] [req: drive-brand-frames] In `drive.py` and `postprocess.py`, resolve the card title from the `change/<slug>` branch, then a supplied title, then a fixed default, and expose the badge corner as an option. Confirm the test file from task 6.6 passes.

## 7. Skill prompt, registration, and documentation

- [x] 7.1 [P1] [req: drive-skill-flow] Write `plugins/s/skills/drive/SKILL.md`: frontmatter `name` and `description` with trigger phrases, the version announcement read from the plugin manifest, the ordered flow (resolve target, preflight, login, session, drive, verdict), the plain-text numbered target round with no `AskUserQuestion`, the probe-before-selecting rule, the wait-for-a-named-completion-signal rule, and the verdict contract.
- [x] 7.2 [P2] [req: drive-skill-flow] Under `plugins/s/skills/drive/references/`, write `recording.md`: the action-module contract, the helper API, and the rule that every reveal the viewer must read is wrapped in a protected hold or an annotation.
- [x] 7.3 [P1] [req: drive-targets-config] Under `plugins/s/skills/drive/references/`, add `targets.example.json` documenting the three auth kinds, with a `command` example built on `op item get` marked as one recipe rather than a requirement.
- [x] 7.4 [P4] [req: drive-skill-flow] Write `plugins/s/harness/bodies/drive.md` with the `<!-- description: ... -->` opening marker and the distilled router content, gating on no feature so no fallback reference file is required. Run `python3 -m unittest discover -s plugins/s/skills/build/tests` and confirm the body-parity test passes with the drive body present.
- [x] 7.5 [P5] [req: drive-skill-flow] Add the `/s:drive` row to the `README.md` Skills table and to `docs/cheatsheet.md`, and name the skill in the `AGENTS.md` command list, each description consistent with the `SKILL.md` frontmatter.
- [x] 7.6 [P6] [req: *] Add a drive test-suite step to `.github/workflows/ci.yml` running `python3 -m unittest discover -s plugins/s/skills/drive/tests -v`, placed after the video-ingest step and requiring no new installation.
- [x] 7.7 [P15] [req: *] Bump the version in `plugins/s/.claude-plugin/plugin.json` from `0.6.206` to `0.6.207`.
- [x] 7.8 [req: *] Run the full CI test set locally — the build, review, video-ingest, document, and new drive suites — plus the master spec lint, and confirm every suite passes.

## 8. Wire the probe verb

- [x] 8.1 [P16] [req: drive-skill-flow] Under `plugins/s/skills/drive/tests/`, add `test_drive_probe.py` covering the control CLI's `probe` verb against an injected runner: it builds a `uv run` invocation of the browser worker's `probe` subcommand carrying the resolved target url and cached storage state; it prints the artifact paths the worker reports; and a worker failure surfaces as one `Error:` line with a non-zero exit. Run it and observe it fail — `cmd_probe` is still a stub.
- [x] 8.2 [req: drive-skill-flow] In `plugins/s/skills/drive/scripts/drive.py`, replace the `cmd_probe` stub (which raises `probe: not implemented yet`) with the real implementation: resolve the target and its cached storage state, invoke the browser worker's already-implemented `probe` subcommand through `uv run`, and print the paths it wrote. Confirm the test file from task 8.1 passes and the whole drive suite stays green.

## 9. Repair the accessibility snapshot against the shipped Playwright

- [x] 9.1 [req: drive-session] In `plugins/s/skills/drive/scripts/browser_worker.py`, replace both `page.accessibility.snapshot(...)` call sites — the session daemon's snapshot handler and the `probe` sampler — with the supported API. Playwright 1.62 removed the `accessibility` namespace entirely (`'Page' object has no attribute 'accessibility'`); use `Locator.aria_snapshot()` on the scoped root instead, storing its returned ARIA tree under the same output key so neither the daemon's JSON reply shape nor `probe`'s reported artifact paths change.
- [x] 9.2 [req: drive-skill-flow] In `plugins/s/skills/drive/scripts/drive.py`, stop double-prefixing a worker failure: the worker already emits `Error: probe failed: <detail>` on stderr, and `cmd_probe` wraps it again, producing `Error: probe failed: Error: probe failed: ...`. Surface the worker's detail once, keeping the single-`Error:`-line convention.
- [x] 9.3 [req: drive-skill-flow] Under `plugins/s/skills/drive/tests/`, add `test_drive_smoke.py`: a live end-to-end smoke test that serves a small static page from a `http.server` thread, runs the real `probe` verb through `uv run`, and asserts the four artifact files exist and the ARIA output is non-empty. Guard the whole case with `unittest.skipUnless` on `uv` being on PATH and a Playwright browser binary being present, so CI (which has neither) skips it and a developer machine runs it. This is the only test shape that can catch a wrong Playwright API; the stdlib-only suites structurally cannot.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 616 | 255.9k |
| Edit | 59 | 65.8k |
| Read | 85 | 45.1k |
| Write | 20 | 38.8k |
| (no tool) | 0 | 7.9k |
| Agent | 7 | 7.4k |
| SendMessage | 4 | 4.8k |
| Monitor | 2 | 663 |
| ToolSearch | 4 | 479 |
| TaskStop | 1 | 58 |
| **Total** | 798 | 427.0k |
