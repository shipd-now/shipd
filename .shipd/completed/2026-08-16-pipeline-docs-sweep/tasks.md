## 1. Format authority grammar (`.shipd/README.md`)

- [x] 1.1 [req: pipeline-grammar-docs] In `.shipd/README.md`'s "The
      autonomous pipeline" section, replace the sentence "`skip`, `tools`,
      and `replace` are mutually exclusive on one entry." with the shipped
      rules: `skip` may only be `true` when present and excludes every
      other field on the entry (options on a skipped stage are an error);
      `tools` and `replace` are mutually exclusive; entries are validated
      strictly — unknown keys and wrongly typed values are rejected, never
      coerced or ignored.
- [x] 1.2 [req: pipeline-grammar-docs] In the same section, add a
      per-stage options subsection: every stage entry may carry `model` (a
      symbolic tier `session`/`tier-below`/`tier-two-below` or a concrete
      model id); `build` additionally accepts `subagent_model` (same tier
      type), `validator` (boolean, default true), `telemetry` (boolean,
      default true), and `parallelism` (integer >= 1); `review`
      additionally accepts `disposition` (`all`/`high-only`/`none`,
      default `all`); any stage or custom entry may carry `autopilot` with
      `attempts` (integer >= 1, default 3), `timeout` (integer > 0), and
      `max_resumes` (integer >= 0). State that defaults are
      schema-declared and never injected: a resolved entry carries exactly
      the keys its author wrote.
- [x] 1.3 [req: pipeline-grammar-docs] In the same section, state the
      pydantic rule: a declared entry list — and every preset but
      `default` — validates through pydantic and fails closed with the
      `pip install -r requirements.txt` hint when it is not importable;
      the absent key and `"default"` resolve without any third-party
      package.

## 2. Follower surfaces

- [x] 2.1 [req: pipeline-follower-docs] In root `README.md`'s
      autonomous-pipeline paragraph (around lines 177-187), add one
      sentence: entries may also carry typed per-stage options (model
      tiers, build's validator/telemetry/parallelism, review's
      disposition, `autopilot` driver knobs), validated strictly — unknown
      keys and wrong types are errors — with a declared list requiring
      `pydantic`; keep the existing link to `.shipd/README.md` as the full
      grammar.
- [x] 2.2 [req: pipeline-follower-docs] In `docs/quickstart.md`'s doctor
      step (around line 44), extend the check list to `python`, `git`,
      `config`, `gh`, `textual`, `pydantic`, `snapshot`, and note
      `pydantic` is needed only for declared-pipeline validation.
- [x] 2.3 [req: pipeline-follower-docs] In `docs/quickstart.md`, add a
      single line mentioning the cheap-delivery opt-in: putting
      `{"autonomous-pipeline": "eco"}` in `.shipd-config.json` runs
      deliveries on the eco preset (place it in the doctor section's
      pydantic note or the "Where to go next" list — wherever it reads as
      one line).
- [x] 2.4 [req: pipeline-grammar-docs] In
      `plugins/s/skills/build/references/shipd.config.example.json`, add a
      `"//"`-style comment line naming the optional `autonomous-pipeline`
      key (a preset name such as `"eco"`, or an entry list; grammar in
      `.shipd/README.md`) without declaring the key itself; keep the file
      valid JSON and the shown values defaults.

## 3. Falsehood corrections

- [x] 3.1 [req: three-strike-parking] Confirm the staged delta retitle
      merges clean: the master requirement `three-strike-parking` in
      `.shipd/verified/epic-autopilot/spec.md` still hashes to
      `78864b825c78`, and the id citations in
      `plugins/s/skills/build/tests/test_autopilot.py` (around line 553)
      need no edit since the id is unchanged. No manual edit to the
      verified spec — the merge engine applies the delta at merge time.
- [x] 3.2 [req: *] In
      `plugins/s/skills/build/scripts/pipeline_schema.py`'s module
      docstring, correct the third-party claim: this module is the
      engine's only pydantic-dependent path; the engine's other
      third-party exception is `textual`, used by `dashboard.py`'s `tui`
      verb (which does not depend on pydantic). Docstring only — no code
      change.
- [x] 3.3 [req: *] In `.shipd/epics/named-pipelines/epic.md`'s Design
      preset table (around lines 133-140), correct the `default` column to
      the shipped truth: bare stage entries as-is — schema defaults
      (validator on, disposition `all`, attempts 3) apply but are never
      injected, and no `subagent_model` or review `model` is set. Leave
      the `eco` and `basic` columns and all archived `completed/`
      artifacts untouched.

## 4. Ship hygiene

- [x] 4.1 [req: *] Bump the patch version in
      `plugins/s/.claude-plugin/plugin.json` (standing convention: every
      change touching `plugins/s/` bumps it).
- [x] 4.2 [req: *] Verification barrier: run `python3 -m unittest discover
      -s plugins/s/skills/build/tests` and confirm it passes unchanged
      (this change edits no engine behavior — comments and docs only), and
      re-read each edited surface against its delta scenarios.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 58 | 21.1k |
| Edit | 11 | 6.5k |
| (no tool) | 0 | 5.5k |
| Read | 12 | 1.7k |
| Agent | 1 | 439 |
| **Total** | 82 | 35.3k |
