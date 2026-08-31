# drop-pydantic
Status: verified
Theme: reliability

## Idea

Replace `pipeline_schema.py`'s pydantic models with a stdlib table-driven
validator and delete every surface that existed to manage the dependency, so
the engine is stdlib-only but for `textual`.

### Motivation

A declared `autonomous-pipeline` fails closed without pydantic, so `/s:plan`
and `/s:build` refuse to start on a machine where the wheel will not install —
a Homebrew Python that PEP 668 blocks, or a Python version with no wheel — and
the documented remedy asks the user to bypass their interpreter's own
protection.

### Details

- Rewrite `plugins/s/skills/build/scripts/pipeline_schema.py` stdlib-only,
  keeping its public API (`validate_entries`, `expand_preset`, `PRESETS`,
  `SYMBOLIC_TIERS`) and its error grammar.
- Drop the `ModuleNotFoundError` fail-closed branches in
  `spec_common.resolve_pipeline` and `spec_status.py`'s `--expand` helper.
- Delete `check_pydantic` and `_pipeline_needs_pydantic` from
  `plugins/s/bin/shipd`, and the `pydantic` entry from `PINNED_SPECIFIERS`.
- Move `tests_pydantic/`'s three suites into
  `plugins/s/skills/build/tests/` and drop the CI step that ran them.
- Drop the pydantic pin from `requirements.txt`, the second dependency
  exception from `.shipd/constitution.md` and `AGENTS.md`, and the pydantic
  prose from `README.md`, `docs/quickstart.md`, the `plan`/`build`/`doctor`
  SKILL files, and `plugins/s/harness/bodies/doctor.md`.
- Bump the plugin version.

Affected capabilities: `shipd-config`, `shipd-cli`, `shipd-doctor`,
`spec-status`, `shipd-plan`, `build-spec-lifecycle`, `project-readme` (all
modified). Impact: `pipeline_schema.py`, `spec_common.py`, `spec_status.py`,
`bin/shipd`, `requirements.txt`, `.github/workflows/ci.yml`,
`.shipd/constitution.md`, `AGENTS.md`, `README.md`, `docs/quickstart.md`,
three SKILL files, one harness body, and the test tree. One dependency
removed; none added.

### Non-goals

- No grammar change. The accepted entry forms, keys, types, bounds, and
  presets stay exactly as they are; only the validating machinery changes.
- No change to `textual`, which stays pinned and stays the engine's one
  dependency exception.
- No change to the `pipeline` doctor check itself — it still resolves and
  still fails on a bad declaration; only its pydantic escalation goes.
- No new config keys, and no change to `resolve_pipeline`'s signature,
  return shape, or provenance strings.

## Implementation

- **The module keeps its name and public API.** `resolve_pipeline` and
  `spec_status.py`'s expand helper keep their call sites; only their
  `ModuleNotFoundError` guards are deleted. Rejected: folding the schema back
  into `spec_common.py` — the module boundary is what keeps the grammar
  reviewable in one file.
- **The lazy import stays.** `pipeline_schema` imports `KEBAB_RE` and
  `PIPELINE_STAGES` from `spec_common`, so a top-level import in
  `spec_common` would be circular. Laziness is now an import-cycle
  requirement rather than a dependency-scoping one.
- **Table-driven, not imperative.** Each entry form declares its keys as data
  — key name to a validator plus whether it is required — and one generic
  walker checks an entry against its form's table. This preserves what
  pydantic actually bought (a declarative grammar that is hard to drift) and
  keeps adding a stage option a one-row edit. Rejected: restoring the
  pre-`6da3864` hand-rolled validator, whose `if`-chains could not express the
  typed per-stage options that motivated the pydantic move.
- **Strictness is explicit.** Unknown keys are rejected; values are checked
  without coercion. `bool` is tested before `int` (in Python `True` is an
  `int`), so `{"skip": 1}` and `{"parallelism": true}` both fail, matching
  pydantic's `strict=True` today.
- **Error grammar preserved, wording free.** Errors keep the shape
  `entry <i> (<compact-sorted-json>): <path>: <message>`, and every offending
  entry is reported. The messages themselves are ours: the ported tests assert
  only semantic needles — `_assert_error` in `tests_pydantic/
  test_resolve_pipeline.py:164` is called with needles like `"retries"`,
  `"entry 0"`, `"fallback"`, `"deploy"` — never pydantic's phrasing. The two
  SKILL files quoting `Extra inputs are not permitted` verbatim are updated to
  the new wording.
- **Defaults are declared but never injected.** `validate_entries` returns
  each entry carrying exactly the keys its author wrote, which pydantic did via
  `exclude_unset=True`; the walker simply copies the input keys.
- **Runnable premises.** `plugins/s/bin/shipd doctor` prints
  `ok pydantic — importable; declared pipelines can be validated`;
  `pipeline-show` on a repo declaring `"eco"` prints all six entries with their
  options; and `validate_entries` was driven on all nine rejected forms to
  capture today's exact messages. The `tests_pydantic` suite currently runs
  98 tests with **9 failures** — see the risk below.

Risk: `tests_pydantic/test_pipeline_show.py`'s 9 failures are not a flake and
not this change's doing. Those tests set `env["HOME"]` to a throwaway
directory to isolate config, which also relocates `USER_BASE`, hiding a
pydantic installed with `pip install --user` (PEP 668's own remedy) from the
subprocess. The suite that proves the pydantic path works is broken by the
install method the doctor recommends. This change removes the cause: once the
validator is stdlib, those tests pass under any `HOME`. Task 3.3 asserts that
rather than leaving it implicit.

Risk: a hand-written walker can drift from the documented grammar where
pydantic's declarative models could not. The 98 ported tests are the guard —
they are behavioral, driving `validate_entries` and `resolve_pipeline` rather
than pydantic internals, so they transfer intact and keep failing on drift.
