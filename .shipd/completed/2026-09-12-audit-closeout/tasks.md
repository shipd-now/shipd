# tasks

- [x] 1.1 [P1] [req: gate-workflow-template] Verify each of the ten restored `gate-workflow-template` scenarios against `plugins/s/integrations/copilot/copilot-review-gate.yml` — triggers, permissions and concurrency; base-ref materialization of the reviewer skill; the pinned CLI version; absolute tool paths, the strictness re-bind and the workspace-file handoff; file-read-not-pipe classification; the fix-required/ship-it status mapping; strict mode's no-status-but-still-comment path; pending-first on pull-request events; and the bridge's reviewer and head guards. Report any scenario whose wording does not match the template rather than editing the template
- [x] 1.2 [P1] [req: board-aggregation, atomic-task-claiming-with-stable-ids, workspace-board-report] Verify the five restored scenarios for `delivery-dashboard`, `build-task-coordination` and `spec-status` against `dashboard.py` (the worktree epic marker), `spec_status.py` (worktree-config skipping during discovery, and show's selection-beats-board precedence) and `claim_task.sh` (content-directory resolution and its default fallback). Report mismatches, do not edit the implementations
- [x] 1.3 [P1] [req: workspace-initialization, workspaces-doc, doctor-verb, config-sample-coverage] Verify the four restored scenarios for `shipd-workspace`, `shipd-cli` and `shipd-config` against `spec_common.py` (the git re-init and ignore-block guards, and the recognized-keys registry), `docs/workspaces/nesting-and-stores.md` (that it documents nesting and external stores), and `plugins/s/bin/shipd` (doctor's dev-mode snapshot branch). Report mismatches, do not edit the implementations
- [x] 2.1 [P2] [req: *] Stop `SessionStartReplacesDifferentTargetTest` in `plugins/s/skills/drive/tests/test_drive_session.py` leaking its replacement stub daemon: the test starts a second session and never stops it, so each full-suite run leaves one `browser_worker.py session` process behind. Add teardown that stops whatever session the test left running, and confirm by running the drive suite twice and checking no stub worker survives
- [x] 2.2 [P2] [req: *] Remove the `Initiative: context-enhancements` line from `.shipd/epics/mikk-knowledge/epic.md`. The named initiative has no brief in this workspace (`.shipd/` holds only `wiki/`), the line arrived with the namespace port, and the epic is complete. Then confirm the library lint exits zero
- [x] 3.1 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/build/tests` and `... -s plugins/s/skills/drive/tests` from the repo root, confirm both pass, and confirm `spec_lint.py audit-closeout` and the bare library lint both exit zero
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` from `0.6.213` to `0.6.214`. This change edits `plugins/s/skills/drive/tests/test_drive_session.py`, and the cached plugin snapshot carries that tests directory, so AGENTS.md's bump rule applies and without it `claude plugin update` would be a no-op against a stale snapshot

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 200 | 72.8k |
| (no tool) | 0 | 2.3k |
| Agent | 4 | 2.2k |
| SendMessage | 1 | 667 |
| Read | 3 | 196 |
| **Total** | 208 | 78.2k |
