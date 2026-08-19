## 1. Render engine

- [x] 1.1 [req: body-render] Add
      `plugins/s/skills/build/tests/test_harness_bodies.py` (unittest
      style) with render-mechanics tests against fixture templates written
      into a temp directory (the module accepts an optional `base_dir`
      argument for exactly this): a gated segment kept iff its feature is
      declared; `else` branch kept otherwise; `include:preamble` resolved;
      marker lines stripped from output; `{refs}` substituted with
      `refs_dir`; `{refs}` in a kept segment with `refs_dir=None` raises an
      error naming the template; an unknown gate name raises `ValueError`
      naming template and line; `commands()` lists ids minus `_` partials;
      `reference()` returns fallback text or `None`; `description()`
      returns a fixture template's declared one-line description and
      `render` strips the description marker. Run the file and
      observe it fail — the module does not exist yet.
- [x] 1.2 [req: body-render] Add
      `plugins/s/skills/build/scripts/harness_bodies.py`: stdlib-only;
      default `base_dir` resolved as `../../harness` relative to the module
      file; whole-line marker parsing (`<!-- if:X -->`, `<!-- else -->`,
      `<!-- end -->`, `<!-- include:preamble -->`, non-nesting); gate names
      validated against `harness_registry.FEATURES` (same-directory
      import); `render`, `commands()`, `reference()`, and `description()`
      per the delta spec (every template opens with a
      `<!-- description: … -->` marker that `render` strips).
      The mechanics tests from 1.1 now pass.

## 2. Body templates

- [x] 2.1 [P2] [req: body-templates, body-content] Under the new
      `plugins/s/harness/` tree (subdirs `bodies/` and `references/`), add
      the shared `_preamble.md` partial (the command-purpose slot and the
      newest-snapshot scripts resolution snippet from `plan.md`'s
      Implementation) and the body + fallback-reference templates for
      `plan`, `build`, `review`, `status` — distilled from each
      `plugins/s/skills/<command>/SKILL.md` under `plan.md`'s distillation
      constraints and per-command core-workflow table; gate build's
      delegated flow on `subagents`, its parallel groups/watch on
      `background-tasks`, plan's interactive round on `question-dialogs`,
      every fallback pointer on `file-references` with inline three-step
      degradation notes in the `else` branches.
- [x] 2.2 [P2] [req: body-templates, body-content] Same, for `doctor`,
      `epic`, `research`, `workspace`, `initiative` (doctor's consent
      round gates on `question-dialogs`).
- [x] 2.3 [P2] [req: body-templates, body-content] Same, for `ask`,
      `teach`, `remember`, `memory`, `forget` (the personal-store and wiki
      flows via `$S/spec_status.py` wiki verbs).
- [x] 2.4 [P2] [req: body-templates, body-content] Same, for `autopilot`,
      `onboard`, `video-ingest`.
- [x] 2.5 [req: body-templates, body-content, body-render] Extend
      `plugins/s/skills/build/tests/test_harness_bodies.py` with the
      real-template integration tests: bodies dir ids equal the
      `plugins/s/skills/` listing; every `if:` gate name is in
      `harness_registry.FEATURES`; every gated template has a
      `references/<command>.md`; every command rendered with an empty
      feature set (and a refs_dir) contains no `<!--`, `{refs}`,
      `subagent`, `sub-agent`, or `AskUserQuestion`; every command
      rendered with the full vocabulary stays under 120 lines; the
      preamble's resolution snippet, run through `sh` against a fake cache
      root holding `0.6.9` and `0.6.10`, resolves under `0.6.10`; the plan
      body invokes `spec_emit.py` and `spec_gate.py` via the scripts
      variable and shares no 10-consecutive-line run with
      `plugins/s/skills/plan/SKILL.md`; fallback pointers appear only when
      `file-references` is declared. Run the tests and fix any template
      that fails them.
- [x] 2.6 [req: *] Run the CI suite command
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v`
      without `textual`/`pydantic` installed and observe all tests pass.

## 3. Ship the snapshot

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      the next patch above the branch's post-base-merge value (expected
      `0.6.139` to `0.6.140`).
