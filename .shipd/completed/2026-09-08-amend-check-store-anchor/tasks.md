## 1. Gate anchoring (spec_status.py)

- [x] 1.1 [req: epic-amend-check-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, extend the
      `epic-amend-check` suite (the class whose fixtures start at
      `_init_repo`/`seed_base`) with a store fixture: a helper that builds a
      consumer git repo and a **separate** store git repo (both on `main`,
      in-repo identity, mirroring `_init_repo`), commits the epic at
      `<store>/specs/<consumer-basename>/epics/e1/epic.md` in the store, and
      writes the consumer's `.shipd-config.json` with the absolute
      `store_root` pointing at `<store>/specs`. Add three tests: (1) an
      uncommitted amendable store edit (stamped Decisions bullet) →
      `epic-amend-check e1 --root <consumer>` exits 0 and reports clean;
      (2) an uncommitted protected store edit (`## Design`) → exit 4 with a
      `protected-section ## Design` line; (3) the store directory outside
      any git work tree → exit non-zero, not 4, with an error naming the
      epic's directory. Run the three tests and observe them fail against
      the current code.
- [x] 1.2 [req: epic-amend-check-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`,
      `cmd_epic_amend_check`: after the `os.path.isfile(path)` check, set
      `anchor = os.path.dirname(path)` and pass `anchor` instead of `root`
      to the three `_git_capture` calls (`rev-parse --show-toplevel`,
      `merge-base HEAD <base>`, `show <sha>:<relpath>`); change the
      not-a-work-tree error to name `anchor` instead of `root`; keep the
      relpath derivation (realpath'd path vs realpath'd toplevel) unchanged.
      Update the docstring: replace the "works identically from the main
      checkout and from a linked amendment worktree" sentence with wording
      that the git calls anchor on the directory holding the epic, so the
      base is read from the repository tracking the epic — the consuming
      repo in-repo, the external store's repository under `store_root`.
- [x] 1.3 [req: epic-amend-check-verb] Run the full
      `plugins/s/skills/build/tests/` suite; confirm the three new tests
      pass and every pre-existing `epic-amend-check` test passes unmodified.

## 2. Store-aware amend flow (docs)

- [x] 2.1 [req: epic-amend-mode] In `plugins/s/skills/epic/SKILL.md`, amend
      mode: after step 1 (resolve and refuse a draft), add the store
      detection — run
      `spec_status.py --root <repo-root> config-show` and check for a
      `store:` line. When present, the flow branches: skip step 2's
      worktree (no `epic-amend-<slug>` worktree, no branch, no PR anywhere);
      make the step-3/4 edits directly in the store's working tree, leaving
      them uncommitted; run step 5's two gates unchanged with `--root`
      still naming the consuming repo, against the uncommitted edit; replace
      step 6 for this case with one local commit in the store's repository
      scoped to the epic file alone, subject `shipd: amend epic <slug>`,
      never pushed, and report the commit hash instead of a PR URL. Note in
      step 5 that a store outside any git work tree makes
      `epic-amend-check` error, which stops the flow per the existing
      non-4-exit rule. Keep the no-store flow byte-identical.
- [x] 2.2 [req: epic-amend-mode] In the same file's header description
      (the frontmatter/description lines summarizing amend mode) and in the
      step-2/step-6 prose, make sure no sentence claims the amendment
      *always* ships as a PR — qualify with the store-case commit path
      added in 2.1.

## 3. Ship hygiene

- [x] 3.1 [req: *] Bump the patch version in
      `plugins/s/.claude-plugin/plugin.json` (read the current value and
      increment the patch component), per the repo's plugin-snapshot rule.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 93 | 23.5k |
| Edit | 13 | 3.4k |
| Read | 13 | 3.0k |
| Agent | 2 | 1.4k |
| ToolSearch | 3 | 1.2k |
| SendMessage | 1 | 402 |
| (no tool) | 0 | 382 |
| Monitor | 1 | 17 |
| **Total** | 126 | 33.3k |
