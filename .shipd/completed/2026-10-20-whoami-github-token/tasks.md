## 1. Test first

- [x] 1.1 [req: room-whoami-verb] In `plugins/s/skills/room/tests/test_room.py`, make "WhoamiTest" clear GH_TOKEN, GITHUB_TOKEN, GH_ENTERPRISE_TOKEN, GITHUB_ENTERPRISE_TOKEN, GH_CONFIG_DIR and GH_HOST from the inherited environment. Extend "test_source_follows_the_environment" with GITHUB_TOKEN-only, GH_TOKEN-over-GITHUB_TOKEN and GITHUB_TOKEN-over-GH_CONFIG_DIR cases, and add "test_enterprise_host_follows_the_enterprise_tokens" on "https://ghe.example.com/o/r/pull/7" plus a GH_HOST case. Assert no token value appears in output. Run it and confirm the new cases fail.
- [x] 1.2 [req: room-whoami-verb] In `plugins/s/skills/room/tests/test_room_run.py`, add a start test asserting the stderr "acting as" line names GITHUB_TOKEN when only it is set, and the value never appears. Run it and confirm it fails.

## 2. Implementation

- [x] 2.1 [req: room-whoami-verb] In `plugins/s/skills/room/scripts/room.py`, add "_room_host(pr, environ)" and rewrite "_credential_source(environ, host)" per plan.md's Implementation; pass the host from "cmd_whoami" and update the docstrings. In `plugins/s/skills/room/scripts/room_run.py`, pass the host on the start line. Run the room suite and confirm it passes.

## 3. Docs and version

- [x] 3.1 [req: room-whoami-verb] Update the source list in `plugins/s/harness/references/room.md` and `docs/agent-identity.md` (add a sentence on the precedence and CI's GITHUB_TOKEN), and run `docs_lint.py` on the doc until it exits 0.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` by one patch. Run every suite CI runs and the spec lint, and confirm they pass.
