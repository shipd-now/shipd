## 1. Implementations

- [x] 1.1 [P1] Create `plugins/s/skills/build/scripts/spec_status.py`
      (stdlib python3, executable): verbs `use <change>`, `current`,
      `show [change]`, `set <status> [change]`, `sync [change]` with the exact
      semantics, defaults, state-file location (`.shipd/state.json`,
      key `current_spec`), output formats, and error behavior fixed in
      design.md D2/D3 and the `spec-status` + `statusline` delta specs.
- [x] 1.2 [P1] Create `plugins/s/integrations/statusline.sh` (bash 3.2-safe,
      executable): stdin session JSON → `workspace.current_dir` (sed,
      fallback `$PWD`); silent exit 0 without `am/spec/changes/`; selection,
      auto-select, `no active specs` / `<n> specs · none selected` fallbacks;
      renders `☢️ <name> · <status> · <done>/<total>` with the ANSI colors
      and omission rules fixed in design.md D4. No Python/Node spawned.
- [x] 1.3 [P1] Extend `plugins/s/skills/build/scripts/spec_lint.py` change
      lint with proposal-header validation per design.md D6 (missing
      proposal.md, title ≠ change slug, missing `Status:` in first five
      non-blank lines, invalid value → errors), and add the
      `# sample-change` + `Status: ready` header to
      `plugins/s/skills/build/tests/fixtures/sample/am/spec/changes/sample-change/proposal.md`
      so the existing suite stays green.

## 2. Tests

- [x] 2.1 [P2] Add `plugins/s/skills/build/tests/test_spec_status.py`
      (stdlib unittest, subprocess against temp repo roots, mirroring
      `test_claim_task.py`): cover use/current round-trip, unknown-change
      rejection, show output shape, set validation and header insertion,
      sync derivation (ready→active→complete, demotion complete→active,
      draft/verified untouched), and no-selection errors.
- [x] 2.2 [P2] Add `plugins/s/skills/build/tests/test_statusline.py`
      (stdlib unittest driving the bash script via subprocess with stdin
      JSON and temp workspaces): cover silent exit outside spec repos,
      rendered line for a selected change (name, status, counts), `?` for
      missing status, auto-select of a sole change, and the none/several
      fallback lines.
- [x] 2.3 [P2] Extend `plugins/s/skills/build/tests/test_spec_lint.py` with
      proposal-header cases: valid header passes, missing Status line fails,
      invalid value fails, mismatched title fails, missing proposal.md
      fails.

## 3. Wiring and docs

- [x] 3.1 [P3] Create `.claude/settings.json` with the `statusLine` entry
      `{"type": "command", "command": "bash plugins/s/integrations/statusline.sh"}`
      (preserving valid JSON if the file exists), and add `.shipd/` to
      `.gitignore`.
- [x] 3.2 [P3] Update `plugins/s/skills/plan/references/emission.md` and
      `plugins/s/skills/plan/SKILL.md`: proposal.md begins with
      `# <change-name>` + `Status: draft`; the approval step promotes to
      `ready` via `spec_status.py set ready <change>`.
- [x] 3.3 [P3] Update `plugins/s/skills/build/SKILL.md`: Phase 3 runs
      `spec_status.py use <change>` and `set active <change>` when spawning;
      Phase 5 runs `sync` after tasks finish and `set verified <change>`
      when verification passes (before Phase 6 merge); Phase 2's go-ahead
      gate sets `ready` when build authored the spec; add the status CLI to
      the "Paths in this skill" list.

## 4. End-to-end

- [x] 4.1 Run the full test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and a
      live smoke: from the repo root, pipe a session JSON with this
      workspace's path into `plugins/s/integrations/statusline.sh` after
      `spec_status.py use spec-status-statusline`, and confirm the rendered
      line shows the change name, its current status, and live task counts.
