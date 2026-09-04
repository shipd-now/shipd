## 1. Cross-universe cat resolution

- [x] 1.1 [req: mediated-read-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing tests:
      `cat epic <slug>` prints an epic hosted only under
      `.worktrees/<name>/.shipd/epics/` (exit 0); when both the root and a
      worktree host the slug, the root's copy prints; `cat change <slug>`
      prints a change hosted only under a worktree's `planned/`;
      `cat research <slug>` prints a report hosted only under a worktree;
      `cat epic no-such` exits non-zero with an error naming the probed
      candidate roots. Run the file and observe the new tests fail.
- [x] 1.2 [req: mediated-read-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, rename
      `_epic_candidate_roots` to public `candidate_roots` (update its
      docstring and every in-file caller: `_epic_hosting_root`, `cmd_locate`,
      `all_epic_slugs_with_roots`), and add a private helper that walks
      `sc.aggregation_universes(root)` × `candidate_roots(universe_root)`,
      applies a per-candidate probe callable, and returns the first hit as
      `(candidate_root, path)` plus the ordered list of probed candidate
      roots, skipping candidates raising `sc.ConfigError`.
- [x] 1.3 [req: mediated-read-verb] In `spec_status.py`'s `cmd_cat`, resolve
      the kinds through that helper: `epic` probes
      `epics/<slug>/epic.md`; `change` probes
      `_readable_change_dir(candidate, slug)`; `verified` probes
      `verified/<slug>/spec.md`; `research` probes
      `research/<slug>/report.md`; `video` probes `video/<slug>/brief.md`.
      Leave `initiative` and `wiki` untouched. On a miss, raise `StatusError`
      naming the slug and the probed candidate roots. Print separators with
      paths relative to the invocation root when inside it and absolute
      otherwise (reuse `_related_path`). Confirm the 1.1 tests pass and the
      existing `cat` tests stay green.

## 2. related spans the invocation universe

- [x] 2.1 [req: related-verb] In `test_spec_status.py`, add failing tests:
      `related <term>` matches an epic hosted only under a worktree (its
      `path` pointing into the worktree); the same `(kind, slug)` present in
      both the root and a worktree yields exactly one row scoring the root's
      copy.
- [x] 2.2 [req: related-verb] In `spec_status.py`'s `_related_corpus`,
      iterate `candidate_roots(root)` (invocation root first), collect each
      candidate's five directory-backed kinds, and skip a `(kind, slug)`
      already collected from an earlier candidate. Keep the wiki surface
      exactly as it is. Confirm the 2.1 tests pass.

## 3. shipd list gains kinds

- [x] 3.1 [req: cli-list, list-json] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add failing tests:
      `shipd list epics --root <repo>` lists a worktree-hosted epic as
      `worktree:<name>` with its `Status:` value; a contested epic slug
      prints once with location `root`; `shipd list verified --root <repo>`
      lists master slugs with status `-`; `shipd list epics --all` exits
      non-zero; `shipd list epics --json` rows carry `name`, `location`,
      `status`, and `project: null`; `shipd list --json` change rows carry
      `project: null`. Keep the existing bare `shipd list` text tests
      unmodified and passing; extend the existing JSON row assertions with
      the new `project: null` key where they compare whole objects.
- [x] 3.2 [req: cli-list] In `spec_status.py`, add a public
      `list_rows(root, kind, span_workspace, include_archived=False)`
      returning ordered `{name, location, project, status}` dicts: `changes`
      reproduces the current planned-directory walk with worktree-wins dedup,
      appending `completed/` rows with status `archived` only when
      `include_archived` is true and the name is not in flight; `epics` walks
      each universe's `all_epic_slugs_with_roots`, reading status with
      `read_epic_status` on the hosting root; `verified`/`research`/`video`
      list slug directories per candidate root-first with status `None`.
      Locations are `root` or `worktree:<name>`; `project` is `None` for the
      own universe and the project slug for a declared universe (spanned only
      when `span_workspace` is true, via `sc.aggregation_universes`). Add
      `test_spec_status.py` coverage for the epics and verified kinds.
- [x] 3.3 [req: cli-list, list-json] In `plugins/s/bin/shipd`, extend
      `cmd_list` with an optional kind positional
      (`changes|epics|verified|research|video`, default `changes`), set
      `--root`'s default to `None` so an explicit flag scopes the listing
      (`span_workspace` false; `None` means cwd with spanning), reject
      `--all` for non-`changes` kinds with an `Error:` line, obtain rows
      from `ss.list_rows`, and render: text status `-` for `None`, foreign
      locations as `<project>:<location>`, JSON rows carrying `name`,
      `location`, `status`, `project`. Delete the now-unused `_probes`,
      `_planned_rows`, `_archived_rows`, and `_collect` helpers and update
      the `USAGE` banner's `list` line. Confirm the 3.1 tests pass.

## 4. explain skill roster

- [x] 4.1 [req: explain-missing-epic] In
      `plugins/s/skills/explain/SKILL.md`, rewrite section 4's fallback
      steps 2–3 to run `"${CLAUDE_PLUGIN_ROOT}/bin/shipd" list epics` for the
      roster instead of `config-show` plus a raw directory listing, delete
      the closing "epic authored in another worktree … is invisible"
      paragraph (lines 173–175) and section 1's parenthetical about the
      roster reading directory names, and keep every other instruction
      unchanged.

## 5. Version bump and verification

- [x] 5.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.175` to `0.6.176`.
- [x] 5.2 [req: *] Run the full suite —
      `python3 -m pytest plugins/s/skills/build/tests/ -q` (no `textual`
      install) — and confirm it passes.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 165 | 25.8k |
| Edit | 35 | 13.1k |
| Agent | 2 | 949 |
| Read | 18 | 882 |
| (no tool) | 0 | 469 |
| Monitor | 5 | 424 |
| TaskStop | 3 | 400 |
| ToolSearch | 2 | 27 |
| **Total** | 230 | 42.1k |
