# Tasks

## 1. Skill and body

- [x] 1.1 [req: gate-update-flow] In `plugins/s/skills/gate/SKILL.md`, add
      the `update` argument dispatch and the refresh-only flow section:
      preflight reuse, the bare `shipd copilot` state read, the
      already-current exit (no write, no commit, no push), the
      `shipd copilot add` refresh with the foreign-file refusal, the commit
      and push of exactly the four managed paths with no further consent
      round, the `shipd-gate-update` pull-request fallback with auto-merge
      attempted and the full URL reported, the closing post-refresh
      state-line relay, and the explicit exclusion of every settings and
      token step. Extend the frontmatter description with the update
      trigger phrases ("/s:gate update", "update the gate").
- [x] 1.2 [req: gate-update-flow] Mirror the same update section in
      `plugins/s/harness/bodies/gate.md`, keeping its
      `<!-- description: … -->` marker a single first line and adding no
      `if:` gates, so the harness-command-bodies contract is unchanged.

## 2. Docs

- [x] 2.1 [req: gate-update-flow] Update the `/s:gate` row in `README.md`'s
      skills table and the `/s:gate` mention in `AGENTS.md`'s skill
      enumeration to name the update flow.

## 3. Verification

- [x] 3.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` by one patch level, so the
      cached plugin snapshot refreshes with this change.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm every test passes — the
      harness-bodies suites cover the edited body template's description
      marker and id-set equality.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Edit | 21 | 16.3k |
| Bash | 49 | 14.6k |
| Write | 1 | 6.5k |
| (no tool) | 0 | 6.0k |
| Read | 16 | 5.2k |
| Agent | 3 | 1.2k |
| AskUserQuestion | 1 | 906 |
| SendMessage | 4 | 892 |
| ToolSearch | 1 | 407 |
| TaskStop | 1 | 63 |
| **Total** | 97 | 52.2k |
