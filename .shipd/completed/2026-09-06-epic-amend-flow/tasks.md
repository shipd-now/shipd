## 1. The epic-amend-check verb

- [x] 1.1 [req: epic-amend-check-verb] Add `EpicAmendCheckTest` to
      `plugins/s/skills/build/tests/test_spec_status.py`: build a temp git
      repo with an in-repo identity (mirror `_init_repo` at
      `plugins/s/skills/build/tests/test_spec_common.py:2466`), commit a
      lint-shaped `epic.md` under `.shipd/epics/<slug>/` on `main`, then
      branch and cover: a Decisions-stamped-bullet plus References-entry
      edit (exit 0, summary, no findings); an `## Introduction` edit
      (`protected-section ## Introduction`, exit 4); a `## Changes` row edit
      (exit 4); a `Status:` line edit (`protected-section header`, exit 4);
      a deleted `## Design` section (exit 4); an epic existing only on the
      branch (exit non-zero error, not 4); an unresolvable `--base` ref
      (exit non-zero error); and a findings run that modifies no file. Run
      the class and observe it fail — the verb does not exist yet.
- [x] 1.2 [req: epic-amend-check-verb] Implement `cmd_epic_amend_check` in
      `plugins/s/skills/build/scripts/spec_status.py`: read the base version
      via `git -C <root> merge-base HEAD <base>` then
      `git show <sha>:<relpath>` (relpath against
      `git rev-parse --show-toplevel`); split both versions into the
      pre-section header block plus level-2 sections using
      `spec_common.SECTION_HEADER_RE`; compare every region outside the
      amendable set (`## Decisions`, `## References`, `## Research`,
      `## Video`); print `protected-section <name>` finding lines (`header`
      for the block before the first section) and a summary; exit 0/4/1 per
      the delta requirement. Register the
      `epic-amend-check <slug> [--base <ref>]` subparser beside
      `epic-sync` (~line 3506), dispatch it (~line 3694), and add the verb
      to the usage epilog listing (~line 56). Confirm the 1.1 tests pass.
- [x] 1.3 [req: epic-amend-check-verb] Document the amendment convention in
      `.shipd/README.md`'s epic section: after the epic-status paragraph
      (~line 836), add an "Amending a live epic" paragraph naming the
      amendable/protected split, the `*(amended YYYY-MM-DD: …)*` stamp, the
      fresh `epic-amend-<slug>` worktree, and the `epic-amend-check` verb.

## 2. The /s:epic amend mode

- [x] 2.1 [req: epic-amend-mode] In `plugins/s/skills/epic/SKILL.md`: add an
      "Amend mode" section gated at the top of the flow (modeled on
      `/s:plan`'s enrichment-mode gate) — when the invocation is
      `<slug> amend`, skip the authoring flow entirely and run: verify the
      epic exists and is not `draft` (refuse a draft, pointing at its
      authoring worktree); create `shipd worktree epic-amend-<slug> --fresh`
      and work inside it; classify the amendment's substance against the
      capture rubric (binding → a stamped `## Decisions` bullet, reference →
      `spec_emit.py docs` + a `## References` link, durable → `/s:teach`,
      noise → dropped); stamp every new or extended Decision with
      `*(amended YYYY-MM-DD: <note>)*` and never rewrite or delete existing
      Decision text; gate on `spec_lint.py --epic <slug>` and
      `spec_status.py epic-amend-check <slug>`; ship per the repository's PR
      workflow with the full URL. Mention the amend mode in the skill's
      frontmatter description.
- [x] 2.2 [req: epic-amend-mode] Mirror the mode in the harness:
      `plugins/s/harness/bodies/epic.md` gains a short amend-mode section
      (same gates, same stamp), and
      `plugins/s/harness/references/epic.md` gains the amend contract — the
      amendable/protected split, the stamp grammar, and the two gates.
- [x] 2.3 [req: epic-amend-mode] Point the existing cross-references at the
      now-real entry point: in
      `plugins/s/skills/epic/references/capture-rubric.md` (~line 34),
      `plugins/s/skills/plan/SKILL.md` (~line 604), and
      `plugins/s/skills/build/SKILL.md` (~line 403), name
      `/s:epic <slug> amend` as the amendment discipline's entry point and
      `epic-amend-check` as its guard, keeping each edit to a sentence.
- [x] 2.4 [req: epic-amend-mode] In `AGENTS.md`, extend the epic-close
      paragraph with the amendment convention: live-epic Decisions/shelf
      edits run through `/s:epic <slug> amend` in a fresh
      `epic-amend-<slug>` worktree and ship as a PR, guarded by
      `epic-amend-check` — never a free edit of the epic file.

## 3. Ship gate

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.6.182 → 0.6.183 (re-check the current value first). Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` (all
      pass, no textual installed) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py --epic
      epic-knowledge --root .` (exit 0).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 89 | 18.0k |
| Read | 36 | 7.2k |
| (no tool) | 0 | 3.3k |
| Edit | 21 | 3.0k |
| Agent | 2 | 1.1k |
| Write | 1 | 467 |
| **Total** | 149 | 33.1k |
