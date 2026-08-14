# Tasks — gate-new-dir-rule

## 1. The relaxed rule

- [x] 1.1 [req: context-sufficiency-checks] In `plugins/s/skills/build/tests/test_spec_gate.py`, add failing tests: a task path one new directory deep (existing grandparent, missing parent — the `plugins/s/skills/research/SKILL.md` shape) produces no finding; a path with parent and grandparent both missing remains a finding whose message names the token and both missing levels; the existing new-file-in-existing-dir and dangling-path tests keep passing.
- [x] 1.2 [req: context-sufficiency-checks] In `plugins/s/skills/build/scripts/spec_gate.py`, extend the file-reference check with the grandparent probe and reword the finding message to "neither its parent nor grandparent directory exists"; bump `plugins/s/.claude-plugin/plugin.json` one patch version. Tests from 1.1 pass.

## 2. Verification

- [x] 2.1 [req: *] Full barrier: unittest suite green; library lint clean; live proof against a copy of the real parked plan — copy `.worktrees/deep-research-skill/.shipd/` from the main checkout into a temp dir (read-only source; never gate the worktree itself, the gate rewrites plans), run the new `spec_gate.py deep-research-skill --root <temp>` there, and confirm the `plugins/s/skills/research/SKILL.md` finding is gone (report whether the copy passes fully or surfaces other genuine findings); remove the temp dir.
