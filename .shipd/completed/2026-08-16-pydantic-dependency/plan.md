# pydantic-dependency
Status: verified
Epic: named-pipelines

## Idea

Ground the named-pipelines epic's pydantic dependency: amend the constitution
with a second scoped exception, pin pydantic in `requirements.txt`, and teach
the `shipd doctor` preflight and the `/s:doctor` remedy table to detect and —
on consent — install it.

### Motivation

The named-pipelines epic validates user-authored pipeline declarations with
pydantic, but the constitution's stdlib-only rule names only `textual` as an
exception and no preflight can detect or remedy a missing pydantic.

### Details

- Amend `.shipd/constitution.md`'s stdlib-only bullet to name two scoped
  exceptions: `textual` (dashboard `tui`) and `pydantic` (declared-pipeline
  validation only).
- Pin `pydantic>=2.12,<3` in `requirements.txt`, extending the existing
  mirror-rule header comment.
- Add a warn-level `pydantic` check to `plugins/s/bin/shipd`'s doctor verb,
  mirroring the `textual` check.
- Add the check and its consent-gated remedy row to
  `plugins/s/skills/doctor/SKILL.md`.
- Update `AGENTS.md`'s third-party-dependency section and the `ci.yml`
  install-step name; bump the plugin version.

Affected capabilities: `shipd-cli` (modified), `shipd-doctor` (modified).
Impact: `.shipd/constitution.md`, `requirements.txt`, `plugins/s/bin/shipd`,
`plugins/s/skills/doctor/SKILL.md`, `AGENTS.md`, `.github/workflows/ci.yml`,
`plugins/s/skills/build/tests/test_shipd_cli.py`,
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No pydantic import lands anywhere in the engine — the validation code that
  uses it is the epic's `pipeline-schema` member, not this change.
- No engine-wide dependency: the stdlib engine suite keeps passing with
  neither `textual` nor `pydantic` installed, and `bin/shipd` itself stays
  stdlib-only (the new check probes via `find_spec`, never imports).
- No automatic install: the doctor remedy stays consent-gated per the
  existing remedy-safety boundaries; the CLI verb itself mutates nothing.

## Implementation

- **Pin `pydantic>=2.12,<3`.** 2.12 is the first line with CPython 3.14
  support and the local interpreter is 3.14.6; pydantic 2.12 supports 3.9+,
  matching the engine's interpreter floor (`PYTHON_FLOOR = (3, 9)` in
  `bin/shipd`). `<3` guards major-version breakage. The range is stated in
  three places that must stay in step — `requirements.txt`, the doctor
  SKILL.md remedy row, and the shipd-doctor delta — following the exact
  precedent of the `textual>=8.2.8,<9` pin and its mirror-rule comment.
- **`check_pydantic` mirrors `check_textual`** (`plugins/s/bin/shipd:328`):
  an `importlib.util.find_spec` probe with injectable `find_spec` for tests,
  warn-level (never `fail`, never affects the exit code), appended to
  `default_checks` after `check_textual` and before `check_snapshot`. The
  probe never imports pydantic, so `bin/shipd` remains stdlib-only and the
  README's "single stdlib-only binary" claim stays true. The warn detail
  names declared-pipeline validation as the only affected surface and hints
  `pip install -r requirements.txt`, matching the textual detail's shape.
- **Doctor skill wiring.** `plugins/s/skills/doctor/SKILL.md` step 2's check
  list gains `pydantic`; the remedy table gains a `warn pydantic` row running
  `python3 -m pip install "pydantic>=2.12,<3"` on consent, with the
  requirements.txt mirror note — the same row shape as `textual`'s. Rejected:
  auto-provisioning a venv like the dashboard's `tui` bootstrap — pipeline
  validation is engine-path code where a silent venv re-exec is unacceptable;
  fail-closed with an install hint is the epic's decided contract.
- **Constitution wording.** The stdlib-only bullet keeps its single-rule
  shape but names two exceptions, each with its scope and the shared
  invariant: every engine script stays importable with neither installed.
  `AGENTS.md`'s "delivery board's one third-party dependency" section is
  reworded to enumerate both pins and their scopes.
- **CI needs no ordering change.** `ci.yml` already runs the stdlib engine
  suite *before* `pip install -r requirements.txt` (proving
  dependency-freeness) and installs the whole requirements file after —
  adding the pin gets pydantic installed for later suites automatically.
  Only the install step's name generalizes.
- **Runnable premise:** `plugins/s/bin/shipd doctor` was run on this machine
  before planning: six `ok` lines (`python`, `git`, `config`, `gh`,
  `textual`, `snapshot`), closing `doctor: ok`, exit 0 — and
  `python3 -c "import pydantic"` fails (ModuleNotFoundError), so after this
  change the same machine observably reports `warn pydantic`.
- **Version bump** in `plugins/s/.claude-plugin/plugin.json` — the change
  touches `plugins/s/`, and the cache snapshot is keyed by version.

Risk: a machine on an older Python where pip resolves no pydantic 2.12
wheel — the check only warns and nothing on the engine path imports
pydantic, so the failure mode is a persistent warn plus a failing remedy
report, never a broken engine.
