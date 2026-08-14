# Tasks — research-fed-epics

## 1. Research link validation

- [x] 1.1 [req: epic-research-link-validation, epic-research-section] In `plugins/s/skills/build/tests/test_spec_lint.py`, add failing tests for the epic `## Research` section: epic-relative link resolves; repo-root-relative link resolves; dead link errors naming the link; existing file outside `<content-dir>/research/` errors; empty `## Research` section errors; epic without the section produces no research finding; a malformed unlinked file under `.shipd/research/` produces no library-lint finding.
- [x] 1.2 [req: epic-research-link-validation, epic-research-section] Implement the check in `plugins/s/skills/build/scripts/spec_lint.py`'s epic validation path (runs in `--epic` mode and library linting): parse `## Research` list entries, resolve each link epic-dir-first then repo-root, require the resolved file to exist under the `specs_dirname`-resolved `research/` folder. Tests from 1.1 pass.

## 2. Skill and docs

- [x] 2.1 [req: research-fed-authoring] Update `plugins/s/skills/epic/SKILL.md`: add the optional `## Research` section to the epic contract (list entries linking research files, epic-relative links shown), and instruct the skill to read supplied/linked research reports as pre-investigation context before its question round, recording every consumed report in the section and never inventing entries.
- [x] 2.2 [req: epic-research-section] Update the epic grammar blurb in `.shipd/README.md` with the optional `## Research` section and the reserved `<content-dir>/research/` home, and bump `plugins/s/.claude-plugin/plugin.json` one patch version.

## 3. Verification

- [x] 3.1 [req: *] Full barrier: run the unittest suite; author a scratch epic fixture with a research link plus a report file under a temp `.shipd/research/` and confirm `--epic` lints clean, then break the link and confirm the error names it.
