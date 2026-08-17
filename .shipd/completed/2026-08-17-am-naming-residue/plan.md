# am-naming-residue
Status: verified

## Idea

Retire the old "am" product name from every live surface it still leaks through — skill announcements, docs, master-spec wording, and the two machine contracts that still carry it — finishing the debt the shipd port knowingly recorded.

### Motivation

The 2026-08-14 port epic renamed the product to shipd but recorded bare `am:<skill>` references and `AM_FLOW_LOG_DIR` as known residuals never assigned to a member, so live sessions still announce themselves as `am:plan v…`/`am:doctor v…` and ~180 stale word-boundary "am" tokens remain across skills, docs, and the master library.

### Details

- Rename the skill self-announcements and cross-references `am:<skill>` → `shipd:<skill>` in the SKILL.md files and the verified requirements that mandate them.
- Fix the `am/constitution.md` path references to `.shipd/constitution.md`, the `.shipd/README.md` title ("# am/ …") and its eval-fixture copies, `docs/portable-workspaces.md`'s `plugins/am`, stale prose ("the lean `am` artifacts", "an am spec-driven build"), engine docstrings, `statusline.sh` comments, and arbitrary `plugins/am` test-fixture paths.
- Migrate the hidden review marker to `<!-- shipd-semantic-review -->` with legacy dual-match, and the flow-log env var to `SHIPD_FLOW_LOG_DIR` with `AM_FLOW_LOG_DIR` fallback.

Affected capabilities: `semantic-review` (modified: gate-poster) and `delivery-metrics` (modified: flow-timeseries) via deltas; ~15 further verified capability specs receive direct wording fixes per the Q1 mechanism. Impact: 10+ `plugins/s/skills/*/SKILL.md`, `plugins/s/agents/*.md`, `plugins/s/integrations/statusline.sh`, engine scripts' docstrings, `review_gate.py` + `tests/test_review_gate.py`, `metrics.py` + `tests/test_metrics.py`, `test_tui_bootstrap.py`/`test_spec_gate.py` fixtures, `.shipd/README.md` + `evals/cases/*/fixture/.shipd/README.md`, `docs/`, plugin version bump.

### Non-goals

- No edits under `.shipd/completed/` — archives are immutable (constitution).
- No edits to `verified/shipd-port`'s legacy-name examples (`am-widget`, `.am-shipd-config.json`, `~/.am-designs/`, the `am-<n>` placeholder) — its scenarios quote the old names by design; rewriting them corrupts the spec that describes the rename.
- No edits to time-of-day "am"/"pm" strings (video pipeline filename handling) or the video vocabulary entries — they are not the product name.
- No hard break of the legacy contracts: the old review marker is still recognized on read, and `AM_FLOW_LOG_DIR` still works as a fallback.
- No fix for the unrelated conflict-marker corruption in `verified/delivery-dashboard` — a separate follow-up change.

## Implementation

- **Announcement format (Q2, oracle-settled).** `shipd:<skill> v<version>` — plain, no ☕ mark: the announcement is a mid-sentence diagnostic flow label, not a brand-mark identity position, and the brand-marks change deliberately enumerated its sites without it. Rejected: `☕ shipd:<skill>` (widens the sanctioned-site set two capabilities just pinned down).
- **Master-sweep mechanism (Q1, oracle-settled).** Direct, boundary-anchored rewrites in `.shipd/verified/*/spec.md` — never bare-`am` substitution, only anchored forms (`am:<skill>`, `` `am` `` as brand prose, `am/constitution.md`) — gated by `spec_lint.py --root .` on the library and the residual scan below. Rejected: per-requirement MODIFIED deltas for wording (the shipd-library-port precedent: bulk rename with structural gates, ceremony reserved for semantic change). The `am/<subdir>` path-prefix notation in master requirement text is retired by this change's `shipd-config` delta (`spec-library-path-notation`): the sweep rewrites those prefixes to `.shipd/` in every capability except `shipd-port` and the delta-owned files. The three delta-owned files (`verified/semantic-review`, `verified/delivery-metrics`, `verified/shipd-config`) are excluded from the direct sweep — their `am` tokens are replaced by this change's deltas at merge.
- **Marker migration.** `review_gate.py` gains `MARKER = "<!-- shipd-semantic-review -->"` and `LEGACY_MARKER = "<!-- am-semantic-review -->"`. Every read-side identification (summary-comment upsert lookup, `reply`/`autoreply`/`resolve` gate-thread recognition) SHALL match a comment carrying either marker; every write emits only the new marker. An existing open PR whose summary carries the legacy marker is therefore edited in place, never duplicated.
- **Env-var migration.** `metrics.py` resolves the flow-log dir as `SHIPD_FLOW_LOG_DIR` when set, else `AM_FLOW_LOG_DIR` (legacy fallback), else the existing config layers; the winning variable's empty string still disables recording. `FLOW_LOG_ENV` becomes the new name plus a `FLOW_LOG_ENV_LEGACY` constant.
- **Residual scan (the completion gate).** After the sweep: `grep -rnw am --include=*.md --include=*.py --include=*.sh --include=*.yml plugins/s docs README.md AGENTS.md install.sh action.yml .shipd/verified .shipd/README.md evals` must return only: `verified/shipd-port` legacy examples, `verified/video-pipeline` + video test/filename "am"/"pm" time strings, video vocabulary list entries, the `LEGACY_MARKER` occurrences this change itself creates (`review_gate.py`, its SKILL.md and tests — the read-side compat contract), the `~/.am/`/`~/.automikk/` legacy-home tokens in the build-reporting negative clauses (`build_report.py`, its tests, and the `verified/build-reporting` spec — they assert those legacy paths are never read or written, so they must keep naming them), and (pre-merge only) the delta-owned marker/env tokens in `verified/semantic-review` + `verified/delivery-metrics` that this change's own deltas retire at merge. Any other survivor is a failure to fix, not a warning.
- **Fixture paths.** `test_tui_bootstrap.py` / `test_spec_gate.py` build fake plugin roots named `plugins/am`; the name is arbitrary — rename to `plugins/s` with assertions unchanged.
- **Version bump.** Read main's current `plugins/s/.claude-plugin/plugin.json` version at build time (0.6.127 at planning) and bump one patch (expected `0.6.128`) — main has moved mid-flight twice today, so the bump is derived, not hardcoded.
- **Runnable premises verified.** `grep -rnw am …` sweeps run this session (186 repo hits; 65 in `verified/`, 17 capability files; shapes categorized by frequency: 17× `am:plan`, 8× `am/constitution.md`, 5× marker, …); `plugins/s/bin/shipd doctor` → exit 0 this turn; build suite last observed 1510 tests OK, review suite 65 OK.

Risk: an anchored substitution touching a string a test asserts verbatim (announcement strings appear in eval fixtures and possibly tests) — bounded by running all CI suites plus the eval fixtures' lint; and the pre-merge residual scan explicitly lists its allowed survivors so nothing is waved through silently.

## Questions and answers

### Q1: How should the master library's stale wording be updated?
- **Question:** ~55 stale "am" brand tokens sit in requirement texts across ~15 verified capabilities. Options: (a) direct mechanical rewrite gated by library lint plus a residual scan, per the shipd-library-port precedent — recommended; (b) full MODIFIED delta ceremony per affected requirement.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a). The shipd-library-port precedent rewrote the whole library via tooling with structural gates and no per-requirement deltas; `spec_merge.py`'s MODIFIED path exists for semantic changes, and none of these edits changes an id, behavior, or scenario. Conditions carried over: boundary-anchored substitutions only (never bare `am`), and any post-run residual outside the deliberate exclusions is a failure, not a warning. The constitution's immutability protects only `completed/`.
- **Cited:** epic/shipd-port, verified/shipd-port, verified/shipd-spec-merge

### Q2: What replaces the `am:<skill>` announcement format?
- **Question:** Skill self-announcements read `am:plan v<version>`. Options: (a) `☕ shipd:plan v<version>`, carrying the brand mark — recommended; (b) plain `shipd:plan v<version>`.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (b) — plain `shipd:<skill> v<version>`, no coffee-cup mark. The brand-marks convention places ☕ only at identity positions directly before the bare product name (titles, brand blocks, completion lines) and deliberately excludes mid-prose and functional labels; the announcement is a mid-sentence diagnostic token for spotting stale snapshots, and the brand-marks change enumerated its sites exhaustively without it.
- **Cited:** epic/brand-marks, verified/shipd-plan, verified/semantic-review, verified/shipd-install, verified/delivery-dashboard, verified/project-readme
