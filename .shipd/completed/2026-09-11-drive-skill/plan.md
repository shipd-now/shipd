# drive-skill
Status: verified

## Idea

Add `/s:drive`, a shipd skill that drives a real browser with Playwright to operate an app, verify a change against it, and record a branded demo video.

### Motivation

shipd plans, builds, reviews, and ships a change, but nothing in the plugin ever opens the app and confirms the change works in a browser — the loop ends at tests and a pull request. The `/s:review` and `/s:fix` skills read code; none of them watch it run.

### Details

- Add `plugins/s/skills/drive/SKILL.md` and its harness body, a new `/s:` command surface.
- Add a stdlib-only control CLI `drive.py` (`doctor`, `targets`, `login`, `session`, the driving verbs, `probe`, `record`, `post`) that shells to Playwright workers through `uv run`.
- Resolve targets and credentials from `~/.shipd/drive/targets.json`, overridden per target by `<content-dir>/drive/targets.json`.
- Hold one browser in a session daemon so console and network evidence accumulates across navigations, and end every run on a PASS/FAIL verdict.
- Record and post-process a demo: cut the leading app boot, play dead-air at 10x, and open on a coffee-mark shipd title card.

Affected capabilities: `shipd-drive` (new), `drive-video` (new). Impact: `plugins/s/skills/drive/` (new tree, scripts flat under `scripts/`), `plugins/s/harness/bodies/drive.md`, `README.md`, `docs/cheatsheet.md`, `AGENTS.md`, `.github/workflows/ci.yml`, and the plugin version bump.

### Non-goals

- No Playwright MCP registration, and no dependency on an MCP server being present in the session.
- No Node.js, npm, `package.json`, or `node_modules` — Playwright arrives as a Python wheel.
- No 1Password dependency: `op` is one documented auth recipe, never a requirement.
- No vendor content — no fixed environment table, no feature-flag injection, no ticket-id derivation.
- No new `.shipd-config.json` key, and no edit to the engine under `skills/build/scripts/`.
- No `AskUserQuestion` dialog anywhere in the skill.

## Implementation

**Runtime — Playwright for Python under `uv run`.** Each worker script carries PEP 723 inline dependencies and runs as `uv run <worker>`, mirroring `plugins/s/skills/video-ingest/scripts/backends/asr_whisper.py`. Verified: `uv run --with playwright python -c "import playwright"` exits 0 and resolves the wheel. The wheel embeds its own driver runtime, so the user installs no Node.js, no npm, and no `node_modules`; nothing is written into the read-only plugin snapshot. Rejected: bundled `.mjs` workers (adds a user-facing Node toolchain); a root `requirements.txt` pin (forces Playwright on every shipd user for one optional skill).

**CLI split.** `drive.py` is stdlib-only and holds every decision — config resolution, auth recipes, cache TTL, the doctor table, the verdict rules, the ffmpeg graphs — so the CI suite tests it with no Playwright installed, exactly as `video-ingest/tests/_stubs.py` stubs `ffmpeg` and `uv` on PATH. The workers hold browser I/O only. `drive.py` reports a fatal error as one `Error: <reason>` line on stderr and a usage error with usage text and exit 2, per `verified/cli-conventions`.

**Session daemon, not per-verb reconnect.** `drive.py session start` spawns `browser_worker.py` as a background process owning one browser, one page, and a Unix socket at `~/.shipd/drive/session.sock`; the driving verbs send one JSON line and read one JSON reply. The daemon attaches `console` and `response` listeners once and accumulates them, so `drive.py console` and `drive.py network` return the complete run log. Rejected: reconnecting over CDP per verb — a fresh connection sees no event emitted before it attached, which is precisely the evidence the verdict rests on.

**Targets and secrets.** `~/.shipd/drive/targets.json` holds `{"authCacheTtlHours": 8, "default": "<name>", "targets": {...}}`; a repo-local `<content-dir>/drive/targets.json` overrides entries by target name. Each target declares `url` plus an `auth` recipe of kind `none`, `env` (two variable names), or `command` (two argv arrays whose stdout is the secret, of which `op item get ...` is the documented example). `drive.py login` passes the resolved secrets to the worker in its environment only — never in argv, never in output — and the worker writes the Playwright storage state to `~/.shipd/drive/auth/<target>.json`, reused while its mtime is inside the TTL. Rejected: a `drive` key in `.shipd-config.json` — `spec_common.py:378` `RECOGNIZED_CONFIG_KEYS` is exhaustive and `verified/shipd-config` (`config-sample-coverage`) enumerates it, so one skill's settings would force a MODIFIED delta on the engine's config contract.

**No dialogs.** Where the request names no target, the skill prints the resolved targets as a numbered plain-text list and reads a typed reply. This follows `verified/shipd-interaction` (`dialog-prose-separation`) and keeps `/s:drive` outside that capability's nine-file AskUserQuestion roster, so no delta on it is needed.

**Verdict.** Verification is on unless the request asks for a demo only. `drive.py console` right after the first navigation is the baseline; only errors absent from that baseline fail the run, warnings never fail, and a 4xx or 5xx response to the target's own origin fails. The run must reach its real completion signal before any verdict is printed.

**Video.** `record_worker.py` runs an action module exporting `run(page, h, base_url)` and emits a semantic timeline — `spans` (waits, fast-forwarded), `holds` (protected reveals, always 1x), and `leadingCut` — into `ff-spans.json`. `postprocess.py` is stdlib-only: it cuts the leading boot, plays every dead-air block of 5s or more at 10x, never cuts interior content, and unions a spinner backstop that keys on the changed-cell union over a time window, which pixel freeze detection structurally cannot see.

**Branding.** The title card renders the wordmark gradient `#8888a0` to `#c6ff4e` (`wordmark.py:50`) on `#0f172a` with the U+2615 coffee mark as its hero glyph. The fast-forward badge is deliberately small and flat: at 1280x720 it is at most 44px tall and 180px wide, carrying `10x` and a single chevron, with no border and no glow.

**Version bump.** Everything lands under `plugins/s/`, so `plugins/s/.claude-plugin/plugin.json` goes `0.6.206` to `0.6.207` in this change.

Risk: a long-lived daemon outliving its session. Guarded by `session status` reporting a stale socket and `session start` reclaiming it.
