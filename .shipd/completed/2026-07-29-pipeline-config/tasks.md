# Tasks — pipeline-config

## 1. Registry and resolver

- [x] 1.1 [req: autonomous-pipeline-key, pipeline-stage-registry, pipeline-entry-validation] In `plugins/s/skills/build/tests/test_spec_common.py`, add failing tests for `resolve_pipeline`: absent key yields all six registry stages in order with default provenance; a declared wholesale list resolves exactly (omitted stages absent, no error, gate included); explicit `skip: true` on the gate resolves skipped; `tools` binding with `fallback: builtin` resolves and carries provenance of the supplying layer; `replace` with `command` + `fallback: skip` resolves; `custom` kebab entry between built-ins resolves at position; errors: unknown stage name (names registry), built-ins out of canonical order, `tools`/`replace` without `fallback` or with an invalid fallback value, `replace` lacking both `command` and `tool`, `custom` with non-kebab name or missing `command`, `skip` combined with `replace`, entry matching no form — each naming the entry index.
- [x] 1.2 [req: autonomous-pipeline-key, pipeline-stage-registry, pipeline-entry-validation] In `plugins/s/skills/build/scripts/spec_common.py`, add `PIPELINE_STAGES = ("research", "epic", "plan", "gate", "build", "review")` and `resolve_pipeline(root)` implementing the closed entry grammar, wholesale semantics, canonical-order check, and provenance return, resolving the key via the existing `resolve_config`. Tests from 1.1 pass.

## 2. The verb

- [x] 2.1 [req: pipeline-show-verb] In `plugins/s/skills/build/tests/test_spec_status.py`, add failing tests for `pipeline-show`: defaults-only prints six stages marked `[default]` and exits zero; a declared pipeline prints the skip, the bindings with fallbacks, and the supplying config path; an invalid pipeline prints every validation error and exits non-zero; the verb runs without a workspace and without a selected change.
- [x] 2.2 [req: pipeline-show-verb] Implement `pipeline-show` in `plugins/s/skills/build/scripts/spec_status.py` over `sc.resolve_pipeline`. Tests from 2.1 pass.

## 3. Docs and plugin

- [x] 3.1 [req: autonomous-pipeline-key] Document the `autonomous-pipeline` key in `.shipd/README.md`'s configuration section (the full example with all five entry forms, wholesale semantics, fallback rule, no-key default) and add a one-paragraph pointer in `README.md`; bump `plugins/s/.claude-plugin/plugin.json` one patch version.

## 4. Verification

- [x] 4.1 [req: *] Full barrier: unittest suite green; library lint clean; live drive — write a scratch `.shipd-config.json` layering a workspace-level pipeline under a repo-level override exercising every entry form, run `pipeline-show` for the valid case (provenance shows the repo layer winning wholesale) and an invalid case (unknown stage errors non-zero), then remove the scratch config.
