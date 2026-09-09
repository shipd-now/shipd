## 1. Engine verb

- [x] 1.1 [req: prd-show-verb] Add `PrdShowTest` to
      `plugins/s/skills/build/tests/test_spec_status.py` (temp workspace
      fixtures, driving the CLI): the slugged report's fields for a
      chain-hosted PRD with and without an `Initiative:` line; a
      `cited-by:` line for a worktree-hosted epic carrying the `PRD:` link
      plus its status; `cited-by: none` when uncited; an unknown slug
      exiting non-zero naming the expected `prd.md` path; the no-workspace
      error; the bare roster with inner-member shadowing of a duplicated
      slug; the empty-store zero-exit report; and both `--json` shapes per
      the delta. Run the class and observe it fail.
- [x] 1.2 [req: prd-show-verb] In
      `plugins/s/skills/build/scripts/spec_status.py` implement
      `cmd_prd_show(root, slug, as_json=False)` per plan.md's Implementation
      (resolve via `sc.resolve_prd`/`sc.prd_path`, header parsing per the
      linter's approach, citing epics enumerated across `candidate_roots`
      via `sc.parse_plan_metadata`, `_emit`-based rendering, the
      `_related_path` path convention), wire the `prd-show` argparse parser
      (optional `slug`, `_add_json_flag`) and dispatch. Confirm the tests
      from 1.1 pass.

## 2. Binary and docs

- [x] 2.1 [req: cli-dispatch] Add a delegation test to
      `plugins/s/skills/build/tests/test_shipd_cli.py` mirroring the
      `search` one (`prd` in the banner `VERBS` tuple; `shipd prd
      no-such-prd` passing through `spec_status.py prd-show`'s `Error:`
      line and exit code) and observe it fail; then add
      `"prd": ("spec_status.py", ["prd-show"])` to `VERB_TABLE` in
      `plugins/s/bin/shipd`, the `prd [slug]` banner line under `epic`'s,
      and `prd` in the trailing "read verbs … accept --json" sentence.
      Confirm the test passes.
- [x] 2.2 [req: prd-user-docs] In `docs/prd.md`, add an "Inspecting PRDs"
      section after the search section — `shipd prd <slug>` with a trimmed
      example report (citing-epics line included), bare `shipd prd` with a
      trimmed roster example, the repo-universe reverse-lookup note, and
      the `shipd render <path>` composition — and name `shipd prd` beside
      `shipd search` in the FAQ's find-it answer. Keep every command
      binary-or-skill.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      the next free patch (0.6.198 if main still sits at 0.6.197).
- [x] 3.2 [req: *] Run the full engine suite
      (`python3 -m unittest discover plugins/s/skills/build/tests`) and
      confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 80 | 22.7k |
| Read | 39 | 4.2k |
| Edit | 13 | 3.4k |
| Agent | 2 | 609 |
| (no tool) | 0 | 154 |
| **Total** | 134 | 31.1k |
