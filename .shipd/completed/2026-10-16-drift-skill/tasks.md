## 1. Contract test

- [x] 1.1 [req: drift-skill-registration, drift-skill-run, drift-skill-verdicts, drift-skill-json]
      Add `plugins/s/skills/build/tests/test_drift_skill_contract.py` in the
      shape of `test_epic_grill_contract.py`: `DriftSkillContractTest` reads
      `plugins/s/skills/drift/SKILL.md` and `plugins/s/harness/bodies/drift.md` and asserts the
      skill's frontmatter holds `name: drift`; both texts (whitespace
      normalized) contain `spec_status.py`, `drift`, `--epic`, `--base`,
      `--json`, `holds`, `revise`, `conflict`, `## Drift verdicts`,
      `verdicts:`, `clean:`, `skipped:`, `cat change`, `cat epic`,
      `cat verified`, `git grep -l -w -F`, and the exit codes `0`, `4`, `1`,
      `2`; the skill text contains none of `AskUserQuestion`, `subagent`,
      `sub-agent`, `git fetch`; the body's first line is a
      `<!-- description: ... -->` marker and the body has no `<!-- if:` line;
      exactly the `drift` skill claims `"/s:drift"` across every
      `SKILL.md` (mirror `TriggerPhraseTest` in `test_harness_bodies.py`);
      and `README.md`, `docs/cheatsheet.md`, `AGENTS.md` each contain
      `/s:drift`. Run `python3 -m unittest
      plugins.s.skills.build.tests.test_drift_skill_contract` and observe the
      failures.

## 2. The skill

- [x] 2.1 [req: drift-skill-run, drift-skill-evidence, drift-skill-verdicts, drift-skill-json]
      Create `plugins/s/skills/drift/SKILL.md` modeled on
      `plugins/s/skills/explain/SKILL.md`: frontmatter `name: drift` and a
      `description: >-` carrying the trigger phrases `"drift"`, `"check
      drift"`, `"has the plan drifted"`, `"/s:drift"`; the version
      announcement (`shipd:drift v<version>`); the read-only contract (no
      file, no mutating verb, no `git fetch`, no re-plan, no gate, no agent,
      no dialog); the `STATUS_CLI` path; then sections exactly as `plan.md`
      "Implementation" specifies: 1 resolve the invocation and strip the
      skill's `--json`; 2 run the verb (text form relayed verbatim, `--json`
      form parsed) and branch on exit `0`/`4`/`1`/`2`; 3 the per-member
      evidence set with the `git` and `cat` commands verbatim, the 400-line
      rule, and the `<sha>:` prefix strip; 4 the verdict rules for `holds`,
      `revise`, `conflict`, the `PLANNER`/`ORACLE` exclusion, and the
      `revise`-on-doubt tie-break; 5 the `## Drift verdicts` block grammar
      with the tally line; 6 `--json` mode with the object shape and the
      error-object rule; Ending naming `spec_gate.py <change>` for `revise`
      and a human decision for `conflict`, then stop.
- [x] 2.2 [req: drift-skill-registration] Create
      `plugins/s/harness/bodies/drift.md` modeled on
      `plugins/s/harness/bodies/status.md`: first line `<!-- description:
      Judge whether an epic's gated plans still hold against main — holds,
      revise, or conflict per drifted member. -->`, a one-paragraph purpose,
      `<!-- include:preamble -->`, then numbered steps condensing 2.1's
      sections 1–6 and the ending, using `python3 "$S/spec_status.py" drift`;
      no `<!-- if:` gate and no `subagent`, `sub-agent`, `AskUserQuestion`,
      `{refs}`. Run `python3 -m unittest
      plugins.s.skills.build.tests.test_harness_bodies` — the parity,
      description, forbidden-token, and ceiling tests pass.

## 3. Registry rows

- [x] 3.1 [req: drift-skill-registration] In `README.md`, after the
      `/s:autopilot` row of the Orchestration table (line 276), add a
      `| \`/s:drift\` | ... |` row describing the skill in one sentence
      (runs `spec_status.py drift`, judges only drifted members, returns
      `holds`/`revise`/`conflict`, read-only).
- [x] 3.2 [req: drift-skill-registration] In `docs/cheatsheet.md`, extend the
      `**Unattended**` group (line 44) to `s:build, s:autopilot, s:drift` and
      add a `| \`/s:drift <change> \| --epic <slug>\` | ... | \`/s:drift
      --epic export-cli\` |` row between the `/s:document` and `/s:drive`
      rows; run `python3 plugins/s/skills/document/scripts/docs_lint.py
      docs/cheatsheet.md` and fix every finding.
- [x] 3.3 [req: drift-skill-registration] In `AGENTS.md`'s skill roll
      (line 157, after the `/s:epic-grill` clause), add `\`/s:drift\` to judge
      whether an epic's gated plans still hold against \`main\``.
- [x] 3.4 [req: drift-skill-registration] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next patch above `main`
      (`0.6.292` at planning time). Re-run 1.1 until it passes.

## 4. Verification

- [x] 4.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and `python3 -m unittest discover -s
      evals/tests`; then `python3 -c "import sys;
      sys.path.insert(0,'plugins/s/skills/build/scripts'); import
      harness_bodies as hb; print(hb.render('drift', ()))"` and confirm the
      rendered body names the verb, the three verdicts, and the tally line.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 57 | 712 |
| (no tool) | 0 | 261 |
| ToolSearch | 1 | 101 |
| TaskStop | 1 | 93 |
| SubagentHandback | 3 | 60 |
| Monitor | 2 | 37 |
| Agent | 3 | 26 |
| **Total** | 67 | 1.3k |
