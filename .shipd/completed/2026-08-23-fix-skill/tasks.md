## 1. Related verb (engine)

- [x] 1.1 [req: related-verb] Add failing tests to
      `plugins/s/skills/build/tests/test_spec_status.py` for the `related`
      verb: ranked keyed-block output across a verified spec and a completed
      change (higher score first; completed slug printed date-stripped),
      ten-block cap with a remainder line at twelve matches, `--json` single
      array with `kind`/`slug`/`score`/`path` keys, no-match single `Error:`
      line with non-zero exit, and absent-workspace silent wiki skip (exit
      `0`, no wiki error). Run them and observe them fail — the verb does not
      exist yet.
- [x] 1.2 [req: related-verb] Implement `related` in
      `plugins/s/skills/build/scripts/spec_status.py`: subparser taking one or
      more terms plus `--json`; corpus walk and per-kind file sets exactly as
      decided in `plan.md`'s Implementation (verified/planned/completed/
      research/epics, wiki via workspace discovery wrapped to skip silently on
      any resolution failure, missing directories skipped); case-insensitive
      per-term substring counts summed per artifact; ordering score desc, then
      kind, then slug; keyed-block printer and JSON mode; no-match
      `StatusError`. Confirm the 1.1 tests pass.

## 2. Curated shipd verb

- [x] 2.1 [req: cli-dispatch] Add failing tests to
      `plugins/s/skills/build/tests/test_shipd_cli.py`: the `shipd --help`
      banner lists `related`, and the `VERB_TABLE` maps `related` to
      `("spec_status.py", ["related"])`. Run them and observe them fail.
- [x] 2.2 [req: cli-dispatch] In `plugins/s/bin/shipd`, add the `related`
      row to `VERB_TABLE`, a `related <terms>` line to `USAGE`, and include
      `related` in the banner's trailing `--json`-capable verb note. Confirm
      the 2.1 tests pass.

## 3. The /s:fix skill

- [x] 3.1 [req: fix-skill-flow] Author `plugins/s/skills/fix/SKILL.md`:
      frontmatter `name: fix` with a description carrying trigger phrases
      ("fix this bug", "debug this", "find and fix", "/s:fix"), and the flow
      per `plan.md`'s Implementation — version announcement, term
      distillation, `related` retrieval and mediated `cat` reads before code
      investigation, reproduce-before-edit, the two-way classification
      (fix + regression test per host testing conventions, re-running the
      reproduction and relevant tests; or stop and hand off to `/s:plan` when
      the documented behavior itself is wrong), the stop-and-report ending
      with no commit/branch/push/PR, and the never-edit-specs rule. Engine
      invocations use `${CLAUDE_PLUGIN_ROOT}` paths as in
      `plugins/s/skills/review/SKILL.md`.
- [x] 3.2 [req: fix-skill-registration] Author
      `plugins/s/harness/bodies/fix.md` as the distilled command body: first
      line `<!-- description: ... -->`, then `<!-- include:preamble -->` and a
      numbered distillation of the skill flow, mirroring
      `plugins/s/harness/bodies/review.md`'s structure (inline else-branches
      for gated features; no separate long-form references file is authored,
      matching the gate command). Run
      `plugins/s/skills/build/tests/test_harness_bodies.py` and
      `test_harness_generate.py`; confirm the bodies/skills id-set equality
      passes.

## 4. Registration and version bump

- [x] 4.1 [req: fix-skill-registration] Add the `/s:fix` row to `README.md`'s
      skills table and add `/s:fix` to `AGENTS.md`'s skill enumeration
      sentence (the "Spec layout and lifecycle" section).
- [x] 4.2 [req: fix-skill-registration] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.147` to `0.6.148`.

## 5. Verification

- [x] 5.1 [req: *] Run the full engine suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`)
      without `textual` or `pydantic` installed and confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 94 | 29.0k |
| Edit | 19 | 19.2k |
| Read | 30 | 6.9k |
| Write | 2 | 6.4k |
| (no tool) | 0 | 5.3k |
| Agent | 2 | 861 |
| **Total** | 147 | 67.7k |
