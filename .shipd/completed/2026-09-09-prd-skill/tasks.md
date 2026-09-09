## 1. The skill

- [x] 1.1 [req: prd-skill-contract] Under `plugins/s/skills/prd/` create
      `SKILL.md` implementing the plan's eleven-point contract exactly
      (frontmatter, role, version announcement, engine paths, workspace
      preflight, codebase-first investigation via the `search` verb,
      standard-default tier selection with announced escalation, the
      multi-round section-by-section interview, compose-and-install through
      `spec_emit.py prd` with `cat prd` read-back, the `/s:epic` ending, and
      question rejection recovery) — sibling style per
      `plugins/s/skills/initiative/SKILL.md` and
      `plugins/s/skills/plan/SKILL.md`; do not add any file under
      `plugins/s/skills/prd/references/`. Then run
      `python3 -m unittest discover plugins/s/skills/build/tests -p
      "test_harness_bodies.py"` and observe the 1:1 guard fail — the body
      does not exist yet.

## 2. The harness body and reference

- [x] 2.1 [req: prd-skill-contract] Under the existing
      `plugins/s/harness/bodies/` directory create the new `prd.md` body (a
      `<!-- description: … -->` first line; the distilled
      router flow; a `question-dialogs` gate around the round vehicle and a
      `file-references` gate around `Read {refs}/prd.md`, each mirroring the
      corresponding block of `plugins/s/harness/bodies/initiative.md`; no
      other gate names) and, under the existing
      `plugins/s/harness/references/` directory, the new `prd.md` fallback
      reference (the PRD header grammar, the status vocabulary `draft`,
      `approved`, `superseded`, the three tiers' exact
      section lists from `spec_common.PRD_TIER_SECTIONS`, and the
      staging-file → `spec_emit.py prd <slug> --from <file>` install rule,
      condensed like `plugins/s/harness/references/initiative.md`). Confirm
      the harness bodies suite now passes, then run
      `claude plugin validate plugins/s` and confirm it passes.

## 3. Roster, version, verification

- [x] 3.1 [req: prd-skill-contract] In `AGENTS.md`'s "Spec layout and
      lifecycle" `/s:` enumeration, add `/s:prd` ("to interview for and
      install a workspace PRD — the discover phase") adjacent to the
      `/s:plan`/`/s:epic` mentions.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      the next free patch (0.6.197 if main still sits at 0.6.196).
- [x] 3.3 [req: *] Run the full engine suite
      (`python3 -m unittest discover plugins/s/skills/build/tests`) and
      confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 87 | 16.2k |
| Edit | 6 | 1.6k |
| Read | 12 | 1.1k |
| Write | 3 | 998 |
| SendMessage | 1 | 695 |
| Agent | 2 | 650 |
| (no tool) | 0 | 163 |
| ToolSearch | 1 | 24 |
| **Total** | 112 | 21.5k |
