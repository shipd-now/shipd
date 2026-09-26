## 1. The printed shape

- [x] 1.1 [req: readiness-attestation] In `plugins/s/skills/plan/references/readiness.md`, under "What you print", change the introducing sentence to say each statement is printed as its own paragraph, separated from the next and from the closing line by a blank line, so a markdown terminal never folds the four together; then edit the fenced template so a blank line sits between each of the four bold statements and before the `Full evidence:` line.
- [x] 1.2 [req: readiness-attestation] In `plugins/s/harness/bodies/plan.md` step 5, after "Print one plain statement per item as visible text" and its backtick shape, add the clause "each statement its own paragraph, separated from the next and from the closing line by a blank line". In `plugins/s/harness/references/plan.md`, in the "What you print." paragraph, add the same clause after the backtick shape. Change nothing else in either file.
- [x] 1.3 [req: readiness-attestation] Run `python3 -m unittest discover -s plugins/s/skills/build/tests -p test_harness_generate.py` and confirm OK, then run `grep -c "blank line" plugins/s/skills/plan/references/readiness.md plugins/s/harness/bodies/plan.md plugins/s/harness/references/plan.md` and confirm each file reports at least 1.

## 2. Version and full suite

- [x] 2.1 [req: *] Run `git fetch origin main`, read `version` from `git show origin/main:plugins/s/.claude-plugin/plugin.json`, and bump `plugins/s/.claude-plugin/plugin.json` to one patch level above it, because this change edits files under `plugins/s/` and the plugin cache snapshot is keyed by version.
- [x] 2.2 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/build/tests` from the repo root and confirm it reports OK.
