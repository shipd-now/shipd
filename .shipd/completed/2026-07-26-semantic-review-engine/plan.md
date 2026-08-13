# semantic-review-engine
Status: verified
Epic: autonomous-delivery

## Idea

PR quality in this repo rests entirely on the `ci` unit suite — nothing
reviews what a change actually does to the code's structure before it
merges. The `autonomous-delivery` epic requires every PR to be gated by ci
plus a CodeRabbit-style, AST-aware semantic review; this change builds the
review engine and its interactive skill, seeded by the user-supplied
`automedifftool` sample code the epic anticipated. The GitHub wiring
(posting, required check) is the separate `semantic-review-gate` member.

Concretely:

- A new `semdiff` engine script at
  `plugins/s/skills/review/scripts/semdiff.py` — a thin mechanical wrapper
  emitting compact JSON: `diff` (syntax-aware structural diff via
  difftastic, with a structural-text fallback), `files` (architectural
  cohort grouping), `context` (best-effort symbol reference lookup),
  `change` (aggregate a planned am change's review context), and `doctor`
  (dependency check with a tiered `--fix` installer for difftastic).
- A new `/s:review` skill at `plugins/s/skills/review/SKILL.md` that
  reviews the working tree (or a base/head ref pair) against a base ref,
  cohort by cohort, with a severity rubric, optional spec-aware
  verification against a planned change, a scannable human report, and a
  `--json` machine mode for the future gate.
- Unit tests for semdiff, ci discovery of them, and the plugin version
  bump.

### Non-goals

- No PR posting, committable suggestions, or required-status-check wiring —
  that is the `semantic-review-gate` epic member, which consumes this
  engine.
- No Jira or external ticket integration.
- No eval case for `/s:review` (deferred to a follow-up change).
- No persisted index or guaranteed call graph — `context` stays best-effort
  on-demand grep.
- No "auto:me" branding or popcorn brand mark — shipd naming only.

Affected capabilities: `semantic-review` (added). Impact: new
`plugins/s/skills/review/` (SKILL.md, `scripts/semdiff.py`, `tests/`);
`.github/workflows/ci.yml` (new test-discovery step);
`plugins/s/.claude-plugin/plugin.json` (0.3.3 → 0.4.0); `AGENTS.md` (skill
roster mention). No third-party dependencies.

## Implementation

- **semdiff is a thin wrapper; judgement lives in the skill.** The script
  only shells out to git/difft/rg and shapes JSON — no findings, no
  severities. Stdlib-only Python 3, matching the engine constitution rule.
  Rejected: putting analysis heuristics in Python — the skill reasons over
  structure; the tool stays testable and dumb.
- **Invocation is `python3 <plugin-root>/skills/review/scripts/semdiff.py`**,
  matching how every other engine script is called. Rejected: a plugin
  `bin/` on PATH — this plugin has no PATH-bin convention.
- **Diff endpoint semantics** follow the sample: no head → working tree vs
  `<base>` (untracked files included); with head → PR-style three-dot
  merge-base by default, `--linear` for two-dot. The JSON echoes resolved
  `base`/`head`/`mode`.
- **Graceful degradation (binding epic decision).** When `difft` is
  missing, `semdiff diff` SHALL NOT die: it falls back to parsing
  `git diff` unified output into the same JSON shape, stamping
  `"engine": "text"` per file and in the summary (`"engine": "difft"` when
  syntax-aware). A per-file difft JSON parse failure also falls back to the
  text engine for that file only. Whitespace-only filtering and
  `signature_changes` estimation run in both engines (text engine matches
  declaration markers against added lines). Rejected: hard-requiring difft
  as the sample does — the epic mandates degradation, and difft is not
  installed on the primary dev machine.
- **Doctor keeps the full tiered installer** (user decision):
  `doctor` reports git (required), difft (recommended — its absence
  degrades, never blocks), rg (optional, `git grep` fallback), gh
  (optional, gate-member concern). `doctor --fix` installs difftastic via
  Homebrew → cargo → prebuilt GitHub release into
  `$CLAUDE_PLUGIN_ROOT/bin` else `~/.local/bin`. Network access happens
  only under `--fix`, never in review subcommands.
- **The am bridge replaces the sample's OpenSpec bridge.** `semdiff change
  <name>` imports `spec_common`/`spec_lint` from
  `../../build/scripts` (sys.path relative to its own file — the
  cross-skill reference into build scripts is the established convention),
  resolves the content dir via the layered config, and emits: the change's
  status, per-capability deltas (operation, requirement id/text, scenario
  texts), `tasks.md` checkbox states with progress counts, lint findings
  for the change, and best-effort impact files (backtick path-like tokens
  from `plan.md`). It errors clearly when the change is not under
  `planned/`. Rejected: shelling out to `spec_status.py`/`spec_lint.py`
  CLIs — in-process import is how engine scripts already share code.
- **Cohort rules** stay segment-aware as in the sample (contracts /
  database / api / frontend / tests, else top-level dir), with one
  shipd addition: paths under a content dir (`.shipd/`) or
  `plugins/*/skills/` map to a `specs` / `skills` cohort respectively, so
  this repo's own changes group sensibly.
- **The skill**: `/s:review` follows the sample's flow — map cohorts
  foundational-first, reason over the structural diff (never dump raw
  files), chase changed signatures through `context`, trace call-site
  values for dead guards and comment drift, report by cohort with the
  high/medium/low severity rubric. Spec-aware mode triggers when the user
  names a change or exactly one change exists under `planned/`: classify
  every delta scenario Met/Unmet/Can't-tell, flag unmet as high-severity
  spec-coverage findings, cross-check task honesty, surface uncovered
  code as observations. Human report: effort score 1–5, a
  `## Findings: ✅ Ship it` / `## Findings: ❌ Fix required` header, a
  `# | rating | details` summary table with 🔴/🟠/🟡 dots, collapsible
  walkthrough, optional mermaid diagrams (dark-mode-safe rgba colors),
  numbered findings by cohort, verdict plus what could not be verified.
  `--json` mode emits only the machine object (verdict
  `pass`/`changes-requested` iff any high/medium finding, findings[],
  spec_coverage[], could_not_verify[]) for the future gate member.
- **Emoji policy**: exactly two sanctioned sites — the ✅/❌ verdict marker
  in the findings header and the 🔴/🟠/🟡 severity dots in the summary
  table. No brand mark, no other emoji anywhere; `--json` output carries
  none. The skill is read-only: it never edits the repo.
- **Tests and ci**: unittest suite at `plugins/s/skills/review/tests/`
  (fixture git repos built in tempdirs; difft-dependent assertions skip
  when difft is absent so ci — which lacks difft — exercises the text
  engine; installer coverage limited to target-triple mapping and install
  dir selection, no network in tests). `ci.yml` gains a discovery step for
  the new tests directory. Rejected: placing tests under `build/tests/` —
  they'd pass discovery unchanged but couple the suites across skills.

Risks: difftastic's JSON display sits behind `DFT_UNSTABLE` and may change
shape — guarded by the per-file text-engine fallback. `rg` may be a shell
shim in Claude sessions — semdiff resolves real binaries via
`shutil.which`, and `git grep` covers absence.
