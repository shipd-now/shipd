# lean-format-drift — tasks

## 1. Terminology and retirement sweep

- [x] 1.1 [P1] In `plugins/s/skills/plan/SKILL.md`, replace the three
      "full-ceremony" phrasings — the frontmatter `description` ("emit the
      full-ceremony am/spec artifacts and stop"), the intro ("emit the
      full-ceremony `am/spec` artifacts, and hand off"), and Flow step 4
      ("**Emit** the full-ceremony artifacts") — with lean wording: "emit the
      lean `am/spec` artifacts (`plan.md`, delta specs, `tasks.md`)" (adapted
      to each sentence). No other content changes.
- [x] 1.2 [P1] In `plugins/s/skills/build/SKILL.md`, reword the Phase 2
      principle line "**The full ceremony below always runs — never
      skipped.**" to "**The full spec workflow below always runs — never
      skipped.**", and in the Operating rules change "The full spec ceremony
      always runs" to "The full spec workflow always runs" if that phrasing
      appears; leave the rest of both sentences intact.
- [x] 1.3 [P1] In the root `README.md` `/s:plan` catalog row, change "emit
      the full-ceremony `am/spec` artifacts and stop" to "emit the lean
      `am/spec` artifacts (`plan.md`, delta specs, `tasks.md`) and stop".
- [x] 1.4 [P1] In `plugins/s/skills/build/scripts/build_report.py`, update
      the two comment/docstring citations "per design.md §1" (line ~183) and
      "per design.md D1/D2" (line ~275) to "per the archived build-report
      design §1" and "per the archived build-report design D1/D2". Comments
      only; no functional change.
- [x] 1.5 [P1] Remove the retired bootstrap-era OpenSpec commands:
      `git rm -r .claude/commands/opsx/` (four files: apply.md, archive.md,
      explore.md, propose.md). Do not touch `openspec/` or anything under
      `am/spec/changes/archive/`.

## 2. Cutover hygiene

- [x] 2.1 Verify: `grep -rn "full-ceremony\|full ceremony" . --include="*.md"
      --include="*.py" --include="*.sh"` shows live hits only under
      `am/spec/changes/archive/`, `openspec/`,
      `am/spec/changes/lean-format-drift/` (this change), and the master
      `am/spec/specs/shipd-plan`/`project-readme` files (expected until the
      merge engine applies this change's deltas); confirm
      `.claude/commands/opsx/` is gone; run `python3 -m unittest discover -s
      plugins/s/skills/build/tests -q` (all green) and `python3
      plugins/s/skills/build/scripts/spec_lint.py lean-format-drift`
      (exit 0).
- [x] 2.2 Bump `plugins/s/.claude-plugin/plugin.json` `"version"` to
      `"0.1.3"`, run `claude plugin marketplace update shipd` and
      `claude plugin update s@shipd`, and verify the snapshot
      `~/.claude/plugins/cache/shipd/am/0.1.3/skills/plan/SKILL.md`
      contains "lean" wording and zero "full-ceremony" matches.
