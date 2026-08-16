# doctor-skill
Status: verified

## Idea

A `/s:doctor` skill that runs the read-only `shipd doctor` preflight,
proposes a remedy per finding, runs the safe remedies with the user's
consent, and re-runs the preflight to show the before/after.

### Motivation

`shipd doctor` diagnoses but — by the shipd-dx epic's deliberate decision —
never mutates, so a newcomer with findings must hand-execute each hint; the
user asked for a consent-gated assisted fix path, and a skill is where
install actions with a conversational consent gate belong.

### Details

- New `plugins/s/skills/doctor/SKILL.md`: run `shipd doctor` (PATH launcher
  first, else `${CLAUDE_PLUGIN_ROOT}/bin/shipd`), parse the spec'd
  `ok|warn|fail <check> — <detail>` lines; all-ok reports and stops;
  otherwise one consent dialog over the runnable remedies, execute only the
  approved ones, re-run doctor, and report before/after.
- Remedy table: `textual` → `python3 -m pip install "textual>=8.2.8,<9"`;
  stale `snapshot` → `claude plugin update s@shipd` (with the
  restart-to-apply note); missing `gh`/`git` → the platform install command,
  run on consent; unauthenticated `gh` → hand the user `! gh auth login`
  (interactive, never run by the skill); `python` version and `config`
  failures → report-only with the exact hint, never auto-fixed.
- The skill joins the interactive set carrying the question-rejection
  recovery rule; README's skills table and AGENTS.md gain the entry;
  `requirements.txt` gains a comment noting the range is mirrored in the
  skill.

Affected capabilities: `shipd-doctor` (added), `shipd-interaction`
(modified). Impact: `plugins/s/skills/doctor/SKILL.md` (new), `README.md`,
`AGENTS.md`, `requirements.txt` (comment only), plugin version bump. No
engine-code changes and no new dependencies.

### Non-goals

- No change to the `shipd doctor` CLI verb — it stays read-only per the
  shipd-dx epic decision; the skill is the only mutating layer.
- No interpreter installs (a failing `python` check is report-only) and no
  edits to any `.shipd-config.json` (a `config` failure is report-only).
- No running of interactive commands (`gh auth login` is handed to the
  user), and no remedy ever runs without explicit consent.
- No `--json` on the doctor verb — the spec'd line format is the parsing
  contract.
- No skill eval case (the evals harness is out of scope for this change).

## Implementation

- **A skill, not `doctor --fix`.** Installing software wants a
  conversational, per-item consent gate; the review engine's
  `semdiff doctor --fix` sets the in-repo precedent that fixes run "only on
  the user's explicit say-so", and the CLI verb keeps its spec'd read-only
  contract untouched. Rejected: a `--fix` flag on `bin/shipd` — it would
  reverse a fresh epic decision for no gain.
- **Parsing contract:** the `shipd-cli` doctor requirement pins the
  `ok|warn|fail <check> — <detail>` line shape and the closing `doctor:`
  line, so the skill parses text; a malformed or absent doctor output is
  reported as its own failure, never guessed past. Binary resolution order:
  `shipd` on PATH (consumer launcher), else
  `${CLAUDE_PLUGIN_ROOT}/bin/shipd` (checkout/snapshot).
- **The textual pin is embedded** as `"textual>=8.2.8,<9"` — the range read
  from `requirements.txt` at planning time — because a marketplace consumer
  has no repo checkout to `-r` from. `requirements.txt` gains a one-line
  comment naming the skill as a mirror so a future pin change updates both.
  Rejected: moving `requirements.txt` into `plugins/s/` — it churns CI,
  AGENTS.md, and the constitution's references for one remedy string.
- **Consent is one batched dialog** (AskUserQuestion, multi-select over the
  runnable remedies, a skip-all option), issued per the
  `shipd-interaction` dialog-prose-separation rule: the findings brief ends
  its turn as plain text when substantive prose is needed, and the dialog
  carries the choices. A rejected/interrupted dialog follows the
  question-rejection recovery rule, which this SKILL.md carries verbatim —
  joining the interactive set the `shipd-interaction` capability
  enumerates.
- **Verified premises:** `shipd doctor` prints the pinned line format and
  `doctor: ok` (exit 0) on this machine; `claude plugin update s@shipd`
  refreshes the snapshot (run this session: 0.6.103 → 0.6.104); the
  requirements range is `textual>=8.2.8,<9` (read from `requirements.txt`).
- **At most one remedy round per invocation** — run doctor, remediate,
  re-run, report; a still-failing check after its remedy is reported with
  the residual hint, never retried in a loop.
- Risk: platform-specific install commands (gh/git) going stale; guard:
  the skill states the command it proposes and runs it only on consent, so
  a wrong guess is visible before it executes.
