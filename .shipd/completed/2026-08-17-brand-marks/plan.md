# brand-marks
Status: verified

## Idea

Carry the ☕ shipd brand mark and a new vector icon across every human-facing surface that shows the product name.

### Motivation

The ☕ coffee-cup brand exists only in the statusline; the README, the review comment posted to GitHub, the delivery-board TUI header, and the installer all present the "shipd" name bare, and the project has no vector brand asset at all.

### Details

- Save the provided coffee-cup SVG as repo-root `icon.svg` and display it in `README.md`, floated beside the banner.
- Prefix the ☕ mark to the shipd name at its brand-mark positions: the README intro, `docs/what-is-shipd.md`'s title, the review summary comment `review_gate.py` posts, the TUI header brand block, and `install.sh`'s completion line.

Affected capabilities: `project-readme`, `semantic-review`, `delivery-dashboard`, `shipd-install` (all modified via added requirements). Impact: `icon.svg` (new), `README.md`, `docs/what-is-shipd.md`, `plugins/s/skills/review/scripts/review_gate.py` (+ its tests and SKILL.md), `plugins/s/skills/build/scripts/dashboard.py` (+ `tests_textual`), `install.sh` (+ `tests/test_install.py`), and the plugin version bump.

### Non-goals

- No change to the statusline — it already carries the ☕ brand.
- No emoji in machine-parsed output: `shipd doctor`'s ok|warn|fail lines, every `--json` payload, the `semantic-review` commit-status context, and the hidden summary-comment marker stay byte-exact.
- No branding of mid-prose "shipd" mentions — only brand-mark positions (titles, brand blocks, completion lines).
- No edits to `docs/quickstart.md` / `docs/getting-started.md` (their titles carry no product name, and the in-flight `getting-started-docs` change owns them) and no ASCII-banner change (verified banner-first invariant — see Q1).
- No icon in PR comments (relative paths do not resolve there) or in the plugin manifest (no icon field in its schema).

## Implementation

- **Brand string.** The mark is the single character `☕` (U+2615, emoji presentation by default, matching `statusline.sh`) plus one space, directly before the name: `☕ shipd`. No variation selector.
- **Icon placement (Q1, oracle-settled).** `icon.svg` lands verbatim at the repo root. README displays it as `<img src="icon.svg" align="right" width="160" alt="☕ shipd">` inserted between the fenced ASCII banner and the intro paragraph, so the banner remains the first rendered block and the twice-verified banner-first invariant (`project-readme`, `shipd-onboard`) is untouched. Rejected: icon above the banner (demotes the invariant); replacing the banner (breaks `shipd-onboard`'s verbatim masthead mirror).
- **Icon source** — `icon.svg` is created with exactly this content:

  ```
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 400" width="100%" height="100%">
    <path d="M 315 160 L 380 160 Q 395 160 395 175 L 395 240 Q 395 250 385 255 L 310 290 L 305 260 L 365 235 L 365 190 L 315 190 Z" fill="#64605D"/>
    <ellipse cx="210" cy="130" rx="113" ry="10" fill="#EFEBE3"/>
    <path d="M 97 130 C 97 140, 323 140, 323 130 L 308 310 C 303 335, 273 335, 210 335 C 147 335, 117 335, 112 310 Z" fill="#76726F"/>
  </svg>
  ```
- **README + docs marks.** README intro `**shipd**` becomes `☕ **shipd**`; `docs/what-is-shipd.md`'s title becomes `# ☕ What is shipd?` and its lead `**shipd**` becomes `☕ **shipd**`.
- **Review summary brand line.** `render_summary` in `review_gate.py` emits `**☕ shipd** semantic review` as the first visible line, between the hidden marker and the `## Findings:` verdict header. The marker stays line 1, so upsert matching is untouched; nothing parses the visible body (status state and disposition come from the JSON, and inline-comment parsing uses its own severity markers), so the added line is safe. The review skill's SKILL.md summary-format description names the brand line.
- **TUI brand block.** `dashboard.py`'s header-bar brand Static becomes `"☕ [$accent bold]shipd[/] [$fg-muted]delivery board[/]"` — the mark precedes the accent name; the header-bar zones are otherwise unchanged.
- **Installer completion line.** `install.sh`'s success line becomes `Installed the ☕ shipd launcher at $LAUNCHER`; the PATH hint, auto-update notice, and error paths are unchanged.
- **Version bump.** `review_gate.py` and `dashboard.py` live under `plugins/s/`, so `plugins/s/.claude-plugin/plugin.json` bumps `0.6.123` → `0.6.124` in this change.
- **Runnable premises verified.** `python3 -m unittest discover -s plugins/s/skills/review/tests` → 62 tests, OK (skipped=1); `python3 -m unittest discover -s plugins/s/skills/build/tests_textual` → 306 tests, OK — the exact CI invocations (`.github/workflows/ci.yml`).

Risk: emoji width quirks when the TUI renders the double-width ☕ glyph — textual handles wide glyphs and the statusline has shipped ☕ already; guarded by the extended `tests_textual` assertion.

## Questions and answers

### Q1: Where does the README icon go relative to the banner-first requirement?
- **Question:** `icon.svg` is displayed in README, but `project-readme` mandates the fenced ASCII banner as the first rendered content. Options: (a) icon above the banner and delta that requirement — initial recommendation; (b) keep the banner first and float the icon beside it; (c) replace the banner with the icon.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (b) — float the icon beside the banner and leave the banner-first requirement untouched. The invariant is verified twice: `project-readme`'s "Banner is the first content" scenario and `shipd-onboard`'s requirement that the tour masthead mirror the README banner verbatim; (a) demotes it for decoration and (c) breaks the mirror outright, while the ☕ identity already lives in the statusline, so the SVG is a complement, not a replacement.
- **Cited:** verified/project-readme, verified/shipd-onboard
