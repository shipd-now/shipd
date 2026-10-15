## 1. Fixtures and the rubric's pure checks

- [x] 1.1 [req: launch-preflight] In
      `plugins/s/skills/build/tests/test_autopilot.py`, after `WaveTest`, add a
      module-level helper `_make_preflight_epic(root, slug, rows, status="ready",
      after=None)` that writes the same stub table `_make_epic` writes but with
      a lint-clean body: `## Introduction` holding one sentence and a
      `### Non-goals` dot-point, `## Decisions` and `## Design` holding one
      sentence each, then `## Changes`. Add `_plant_stamped(root, slug,
      status="ready", under=None, gated_hash="0123456789ab", modifies=(),
      cites=())` writing `plan.md` with `Status: <status>` and, when
      `gated_hash` is not `None`, a `Planned-at: <40 a's>` and `Gated-hash:
      <gated_hash>` line under it; `tasks.md` with one `- [ ] 1.1 [req: x]`
      task citing each backticked path in `cites`; and for each
      `(capability, req_id, op)` in `modifies` a `specs/<capability>/spec.md`
      holding a `## <op> Requirements` section with a `### Requirement:`
      block carrying `id: <req_id>` and, for `MODIFIED`/`REMOVED`, `base:
      000000000000`. Add a `_PreflightCommands` fake with `__init__(self,
      check=None, drift=(0, "", ""), doctor=(0, "", ""))` whose `__call__(cmd,
      cwd)` records `(cmd, cwd)` and returns `check[slug]` (default `(0,
      "PASS (check)", "")`) when `"--check" in cmd` with `slug` the argv
      element after the script path, `drift` when `"drift" in cmd`, and
      `doctor` when `cmd[-1] == "doctor"`. Add class
      `PreflightTest(AutopilotTestBase)` with `_run(self, slug="ep",
      commands=None)` returning `autopilot.compute_preflight(self.root, slug,
      command_fn=commands or _PreflightCommands())` and `_line(self, result,
      check)` returning the first check dict whose `check` equals `check`.
      Add tests: a `_make_preflight_epic` with members `a`, `b` both
      `_plant_stamped` ready with disjoint `modifies` and `cites` and a
      doctor fake printing `ok git — found\ndoctor: ok\n` → every check level
      is `ok`, `result["failed"]` is `False`, `result["problems"] == 0`, and
      the check names in order are `epic-lint`, `epic-status`, `after-cycle`,
      `members`, `gate-check`, `gated-hash`, `drift`, `overlap-requirements`,
      `overlap-files`, `pipeline`, `doctor:git`; an epic at `draft` →
      `epic-status` is `fail` and its detail names `epic-set-status`; an
      epic written with `_make_epic` (no required sections) → `epic-lint` is
      `fail`; `after={"x": ["y"], "y": ["x"]}` → `after-cycle` is `fail` with
      detail containing `x -> y -> x`, and the result still has every check
      name; one member unplanned and one `_plant_stamped(status="draft")`
      → `members` is `fail`, its detail contains `unplanned: `, `draft: `,
      and `/s:epic-grill ep`; a `rejected` member → `members` detail
      contains `/s:plan <slug>`; an `active` member → `members` is `warn`;
      a missing `<tmp>/epics/ep/epic.md` → `compute_preflight` raises
      `AutopilotError`. Run `python3 -m unittest
      plugins.s.skills.build.tests.test_autopilot.PreflightTest` and observe
      the failures.
- [x] 1.2 [req: launch-preflight] In
      `plugins/s/skills/build/scripts/autopilot.py`: add `import re`; extend
      the `spec_lint` import to `from spec_lint import lint_change,
      lint_epic`; add constants `STATUS_PY = os.path.join(SCRIPTS_DIR,
      "spec_status.py")`, `SHIPD_BIN = os.path.join(PLUGIN_DIR, "bin",
      "shipd")`, `DOCTOR_LINE_RE = re.compile(r"^(ok|warn|fail) (\S+) — (.*)$")`,
      and `PREFLIGHT_CHECKS = ("epic-lint", "epic-status", "after-cycle",
      "members", "gate-check", "gated-hash", "drift", "overlap-requirements",
      "overlap-files", "pipeline")`. Under a new "Launch preflight
      (epic-autopilot launch-preflight)" section after `compute_waves`, add
      `_pf_level(findings, failing, warning)` returning `"fail"` when
      `failing`, `"warn"` when `warning`, else `"ok"`; `_after_reach(after_map)`
      returning `{slug: set of every slug reachable through After edges}`;
      `_pf_ordered(reach, a, b)` returning `b in reach[a] or a in reach[b]`;
      and `compute_preflight(root, epic, command_fn=None)` that raises
      `AutopilotError("epic not found: %s" % epic)` when `_epic_file` is
      missing, reads the epic text, builds `members = parse_members(root,
      epic)` with each member's hosting root from
      `ss._member_state_with_root`, and appends the first four checks per
      `plan.md` "The checks" (`epic-lint` via `lint_epic(root, epic, errors)`;
      `epic-status` via `ss.read_epic_status`; `after-cycle` via
      `sc.find_after_cycle(sc.parse_epic_after(text))`; `members` grouping
      states as `plan.md` specifies). Return `{"epic": epic, "checks":
      checks, "problems": <count of non-ok>, "failed": <any fail>}`. Re-run
      1.1 until the tests for these four checks and the error pass; the
      remaining checks come in sections 2 and 3.

## 2. Gate, drift, and doctor through the command seam

- [x] 2.1 [req: launch-preflight] In `PreflightTest`, add tests: a ready
      member whose `check` fake returns `(2, "REJECTED (check): ... (1
      finding(s)):\n- gated-hash mismatch: plan.md was edited after it was
      gated (stamp a, content b); re-gate with spec_gate.py a\n", "")` →
      `gated-hash` is `fail` with detail containing `a` and `spec_gate.py a`,
      and `gate-check` is `ok`; a ready member whose check returns `(2,
      "REJECTED (check): ... (1 finding(s)):\n- tasks.md cites nope.py, which does not exist\n", "")` → `gate-check` is `fail`
      naming the member and `nope.py`; a check returning `(1, "",
      "Error: boom")` → `gate-check` is `fail` with detail containing `exit
      1`; a ready member planted with `gated_hash=None` → `gated-hash` is
      `warn` naming the member; the recorded `--check` call runs
      `[sys.executable, autopilot.GATE_PY, slug, "--root", <hosting root>,
      "--check"]` in the hosting root, and a member planted `under="wt"` is
      checked with `<tmp>/.worktrees/wt` as its root; `drift=(4,
      json.dumps({"epic": "ep", "base": {"ref": "main", "sha": "x"},
      "members": [{"change": "a", "findings": [{"kind": "file-drift"},
      {"kind": "file-drift"}, {"kind": "symbol-gone"}]}, {"change": "b",
      "findings": []}], "skipped": []}), "")` → `drift` is `warn` with detail
      containing `a (file-drift 2, symbol-gone 1)` and `/s:drift ep` and not
      `b (`; `drift=(1, "", "Error: unknown base")` → `drift` is `fail`;
      `drift=(0, "{...clean...}", "")` → `drift` is `ok`; the recorded drift
      call is `[sys.executable, autopilot.STATUS_PY, "--root", root,
      "drift", "--epic", "ep", "--json"]`; `doctor=(0, "ok git —
      found\nwarn protection — unprotected\ndoctor: 1 problem(s)\n", "")` →
      the result holds `ok doctor:git — found` and `warn doctor:protection —
      unprotected` as check dicts and no check named `doctor:` or
      containing `problem(s)`; `doctor=(1, "fail gh — not
      authenticated\ndoctor: 1 problem(s)\n", "")` → `doctor:gh` is `fail`
      and `result["failed"]` is `True`; `doctor=(127, "", "no such file")` →
      one check `doctor` at `fail` with detail containing `no such file`;
      the recorded doctor call is `[sys.executable, autopilot.SHIPD_BIN,
      "doctor"]` in `root`. Run and observe the failures.
- [x] 2.2 [req: launch-preflight] In `autopilot.py` `compute_preflight`,
      after the `members` check: for each member at `ready` (table order),
      run `command_fn([sys.executable, GATE_PY, slug, "--root", hosting,
      "--check"], hosting)`; collect the dot-point lines (`- ` prefix) of
      stdout into `mismatch` (lines containing `gated-hash mismatch`) and
      `other`; a `rc` of 0 is clean, 2 reports `other`, any other `rc`
      reports `"<slug>: spec_gate.py --check exit <rc> <first stderr line>"`
      under `gate-check`. Append `gate-check` (`fail` with `; `-joined
      `"<slug>: <first other finding>"` entries, else `ok "<n> ready
      member(s) pass spec_gate.py --check"` or `ok "no ready member"`), then
      `gated-hash` (`fail` `"<slug>: plan.md edited after it was gated;
      re-gate with spec_gate.py <slug>"` per mismatch; `warn` `"<slug>: no
      Gated-hash stamp; gate it with spec_gate.py <slug>"` when
      `sc.read_plan_stamp(plan text)[1]` is `None`; else `ok "<n> stamped
      member(s) match"`). Then run `command_fn([sys.executable, STATUS_PY,
      "--root", root, "drift", "--epic", epic, "--json"], root)`: `rc` 0 →
      `ok "no drift since the plan stamps"`; `rc` 4 → parse stdout as JSON
      and `warn` with `", "`-joined `"<change> (<kind> <n>, ...)"` for each
      member with findings (kinds in first-seen order) followed by `" —
      judge with /s:drift <epic>"`; any other `rc` or unparseable JSON →
      `fail "drift verb exit <rc>: <first stderr line>"`. Then the
      `overlap-requirements`, `overlap-files`, and `pipeline` checks (append
      them as `ok` stubs that 3.2 replaces). Finally run
      `command_fn([sys.executable, SHIPD_BIN, "doctor"], root)`, append one
      check `(level, "doctor:" + name, detail)` per stdout line
      `DOCTOR_LINE_RE` matches, ignoring every other line, and when no line
      matches append `("fail", "doctor", "shipd doctor exit <rc>: <first
      stderr line or stdout line>")`. Re-run 2.1 until it passes.

## 3. Overlap and pipeline checks

- [x] 3.1 [req: launch-preflight] In `PreflightTest`, add tests: ready `a`
      and `b` both `modifies=[("cap", "req-one", "MODIFIED")]` and no `After`
      → `overlap-requirements` is `fail` with detail containing `a & b` and
      `a & b: cap/req-one`; the same with `after={"b": ["a"]}` → `ok`; `a` MODIFIED
      and `b` REMOVED of the same id → `fail`; `b` RENAMED from `req-one`
      (write a `## RENAMED Requirements` section with `- FROM: req-one` /
      `- TO: req-two`) while `a` modifies `req-one` → `fail`; `c` after `b`,
      `b` after `a`, `a` and `c` sharing a requirement and a cited path →
      both overlap lines `ok`; `a` and `b` both `cites=["src/engine.py"]` →
      `overlap-files` is `warn` with detail containing `a & b` and
      `a & b: src/engine.py`, `result["failed"]` stays `False`, `problems` is 1;
      both citing only `plugins/s/.claude-plugin/plugin.json` and
      `cites=["artefacts/x.md"]` → `overlap-files` is `ok`; a `draft` member sharing a
      requirement with a ready one → still reported under
      `overlap-requirements`; `pipeline` is `ok` with detail containing
      `6 entries` and `source: default`; a root whose `.shipd-config.json`
      declares `"autonomous-pipeline": [{"stage": "build", "validater":
      false}]` → `pipeline` is `fail` with detail containing `validater`.
      Run and observe the failures.
- [x] 3.2 [req: launch-preflight] In `autopilot.py`: add
      `_member_delta_targets(hosting, slug)` returning the ordered set of
      `"<capability>/<id>"` for every `modified` and `removed` entry's `id`
      and every `renamed` entry's `from_id` across `sc.parse_delta` of each
      `planned/<slug>/specs/*/spec.md` under `sc.specs_dir(hosting)`; add
      `_member_cited_paths(hosting, slug)` returning the ordered set of
      `sc.cited_paths(text, strip_line_suffix=True)` over `plan.md`,
      `tasks.md`, and every `specs/*/spec.md`, dropping tokens starting with
      `artefacts/` and tokens in `sc.VERSION_BUMP_EXEMPT_PATHS`. In
      `compute_preflight`, over the planned members (state not `unplanned`
      or `archived`, table order) build `reach = _after_reach(after_map)`
      and, for each unordered pair `(a, b)` in table order (`not
      _pf_ordered(reach, a, b)`), report every shared target as `"a & b:
      <target>"` under `overlap-requirements` (`fail`, `; `-joined, else `ok
      "no shared master requirement among unordered members"`) and every
      shared path as `"a & b: <path>"` under `overlap-files` (`warn`, else
      `ok "no shared cited file among unordered members"`). Add the
      `pipeline` check: `entries, provenance = sc.resolve_pipeline(root)` →
      `ok "<n> entries (source: <provenance>)"`, `sc.ConfigError` → `fail
      str(exc)`. Update the module docstring with a paragraph on
      `--preflight`. Re-run 3.1 until it passes.

## 4. CLI, version, verification

- [x] 4.1 [req: launch-preflight] In `PreflightTest`, add CLI tests that
      patch `autopilot._run_command` with a `_PreflightCommands` instance for
      the call: `main(["ep", "--root", root, "--preflight"])` on the green
      fixture returns 0 and stdout ends with `preflight: ok`; with one
      unplanned member it returns 1, stdout holds a line starting `fail
      members — ` and ends with `preflight: 1 problem(s)`; `--preflight
      --json` prints one object with `epic`, `checks`, `problems`, `failed`;
      `--preflight --waves`, `--preflight --dry-run`, and `--preflight
      --member a` each raise `SystemExit` with code 2; after a `--preflight`
      run no `.shipd/autopilot` directory and no `.worktrees` directory
      exist under the root. Run and observe the failures.
- [x] 4.2 [req: launch-preflight] In `autopilot.py`: add
      `_print_preflight(result, as_json=False, out=print)` printing
      `json.dumps(result)` under `as_json`, else one `"%s %s — %s"` line per
      check then `preflight: ok` or `preflight: <problems> problem(s)`; add
      `parser.add_argument("--preflight", action="store_true", help="print
      the launch rubric (ok|warn|fail per check); drive nothing")`, change
      the `--json` help to "with --waves or --preflight, print one JSON
      object", and add `parser.error("--preflight drives nothing; it cannot
      be combined with --waves, --dry-run or --member")` when `args.preflight`
      meets any of the three; dispatch `--preflight` before `--waves` in the
      `try` block as `result = compute_preflight(root, args.epic);
      _print_preflight(result, as_json=args.json); return 1 if
      result["failed"] else 0`. Re-run 4.1 until it passes.
- [x] 4.3 [req: launch-preflight] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next patch above the value
      on `main` at build time (`0.6.292` when this plan was written; rebase
      and re-bump if a sibling member landed first).
- [x] 4.4 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and `python3 -m unittest discover -s
      evals/tests` from the worktree root and confirm every test passes;
      then run `python3 plugins/s/skills/build/scripts/autopilot.py
      autopilot-preflight --preflight` and `... --preflight --json` from the
      worktree root and confirm the text form prints one line per check
      ending in a `preflight:` summary with `doctor:`-prefixed lines, the
      JSON form parses as one object, and the exit code is 1 because this
      epic still has unplanned members.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 80 | 1.1k |
| (no tool) | 0 | 385 |
| ToolSearch | 2 | 179 |
| TaskStop | 1 | 93 |
| SubagentHandback | 4 | 63 |
| Agent | 4 | 62 |
| Monitor | 2 | 37 |
| **Total** | 93 | 1.9k |
