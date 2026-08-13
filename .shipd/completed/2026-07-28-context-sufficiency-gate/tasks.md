# Tasks — context-sufficiency-gate

## 1. The rejected status

- [x] 1.1 [req: proposal-status-header, status-lifecycle-stages, transition-guards, status-cli] In `plugins/s/skills/build/tests/test_spec_status.py` and `test_spec_lint.py`, add failing tests: `rejected` accepted by `set-status` with no structural guard (even on a structurally broken change), `sync` leaves a `rejected` plan untouched, `set-status` still rejects unknown values naming all six, and change lint accepts `Status: rejected` plus a `## Context insufficient` section while still erroring on unknown statuses.
- [x] 1.2 [req: proposal-status-header, status-lifecycle-stages, transition-guards, status-cli, proposal-header-validation, plan-document-sections] Add `rejected` to `STATUSES` in `plugins/s/skills/build/scripts/spec_status.py` (guards: none for `rejected`; `sync` exclusion) and to `VALID_STATUSES` in `spec_lint.py` (plus tolerating the pre-Idea `## Context insufficient` section). Tests from 1.1 pass.
- [x] 1.3 [req: status-lifecycle-stages] In `test_statusline.py`, add a failing test rendering a `rejected` change (red status segment), then add `rejected` to the status case and `status_color` (`\033[31m`) in `plugins/s/integrations/statusline.sh`. Tests pass.

## 2. The gate

- [x] 2.1 [req: context-gate-verb, context-sufficiency-checks, ephemeral-insufficiency-report] Add `plugins/s/skills/build/tests/test_spec_gate.py` with failing tests: pass path promotes `draft` to `ready`, removes a stale `## Context insufficient` section, exits 0; each context check rejects (stale `base:` hash, each placeholder marker word-bounded and case-insensitive, unresolvable backticked task path with `/`, new-file-in-existing-dir passing, MODIFIED delta against a missing capability); failing run writes the section after the header metadata and before `## Idea` with a summary paragraph plus per-finding dot-points, sets `rejected`, exits 2; re-gate replaces the section without accumulating; header title/`Status:`/`Epic:` lines preserved byte-for-byte; unknown change exits 1.
- [x] 2.2 [req: context-gate-verb, context-sufficiency-checks, ephemeral-insufficiency-report] Implement `plugins/s/skills/build/scripts/spec_gate.py` (stdlib only): run `spec_lint.lint_change` plus the four context checks from the delta, write/remove the plan section, and drive status through `spec_status`'s metadata-preserving machinery. Tests from 2.1 pass.

## 3. Docs and plugin

- [x] 3.1 [req: status-lifecycle-stages] Update the status pipeline docs to six statuses with the gate flow: `README.md` (lifecycle + statusline sections), `.shipd/README.md` (status vocabulary and the gate-owned `## Context insufficient` plan section), `docs/onboarding/02-artifacts.md` (pipeline list), and `plugins/s/skills/status/SKILL.md` if it enumerates statuses; bump `plugins/s/.claude-plugin/plugin.json` one patch version.

## 4. Verification

- [x] 4.1 [req: *] Full barrier: unittest suite green; library lint clean; live drive on a scratch repo — author a deliberately context-starved change (TODO marker + bogus task path + stale base), run `spec_gate.py`, confirm `rejected` + the in-plan section + exit 2 and the statusline's red render, then enrich it and confirm a re-gate promotes to `ready`, removes the section, and exits 0.
