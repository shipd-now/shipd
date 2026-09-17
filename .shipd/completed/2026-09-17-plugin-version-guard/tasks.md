- [x] [req: plugin-version-advance] In
      `plugins/s/skills/build/scripts/version_guard.py`, add the stdlib-only
      guard: a version comparison that splits on `.` and compares components
      as integers where both parse, a finding function taking base version,
      head version and touched paths, and a `--base`/`--head` CLI resolving
      both from git and exiting 0, 1, or 2 as specified.
- [x] [P1] [req: plugin-version-advance] In
      `plugins/s/skills/build/tests/test_version_guard.py`, cover the finding
      function directly, with no git and no network: unchanged version with a
      plugins/s path, bumped version, path outside the plugin, manifest-only
      path, `0.6.9` to `0.6.10`, and a decrease.
- [x] [P1] [req: plugin-version-advance] In `.github/workflows/ci.yml`, set
      the checkout step's `fetch-depth: 0` and add a `Guard the plugin
      version` step running the script against the pull request's base branch,
      conditioned on the event being a pull request.
- [x] [P1] [req: plugin-version-advance] In
      `plugins/s/.claude-plugin/plugin.json`, set the version to `0.6.223`.
- [x] [req: plugin-version-advance] Run the engine test suite and the new
      guard against this branch's own base to confirm it passes on a change
      that does bump the version; fix any failure.
