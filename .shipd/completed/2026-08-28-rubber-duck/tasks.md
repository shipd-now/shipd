## 1. The /s:duck skill

- [x] 1.1 [req: duck-critic-session] Create `plugins/s/skills/duck/SKILL.md`
      following sibling conventions (read `plugins/s/skills/ask/SKILL.md`
      first): frontmatter (`name: duck`, `description` with trigger phrases —
      "rubber duck", "talk through this idea", "validate this concept",
      "/s:duck"), the first-reply banner `🦆 Rubber Duck agent — shipd:duck
      v<version>` with the version read from
      `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and no banner on
      later replies, and the read-only contract: may read the repo and
      `spec_status.py cat` surfaces; never edits or creates files, runs
      mutating commands, emits artifacts, or invokes another skill; an
      implementation request is declined with the matching skill named. Cite
      the installed report `.shipd/research/ai-rubber-duck-dx/report.md` as
      the design source in one line.
- [x] 1.2 [req: duck-critique-discipline] In that SKILL.md, write the critique
      protocol exactly per the plan's Implementation: push back rather than
      agree, surface the strongest alternative when one exists, at most three
      critique points per reply each labeled blocking / non-blocking /
      suggestion, suppress style and naming trivia, end every reply with
      exactly one primary question, and honor verbal intensity cues ("go
      easy" / "grill me") with no formal intensity argument.
- [x] 1.3 [req: duck-handoff] In that SKILL.md, add the exit map and wrap-up
      debrief: un-cited external unknowns → `/s:research`, multi-change
      feature → `/s:epic`, single buildable change → `/s:plan`, reported
      defect → `/s:fix`, decision wanting mikk's standing opinion → `/s:ask` —
      each named, never invoked; on a wrap-up cue print the debrief (problem,
      options considered, recommendation with rationale, known risks, next
      command) as response text, writing no file.

## 2. Harness body

- [x] 2.1 [req: duck-harness-body] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests -p "test_harness_bodies.py"` and observe
      the roster-parity failure now that `plugins/s/skills/duck/` exists
      without a body template.
- [x] 2.2 [req: duck-harness-body] Create `plugins/s/harness/bodies/duck.md`:
      first line a `<!-- description: Talk an idea through with the
      adversarial Rubber Duck agent — read-only critique, nothing changed. -->`
      marker, then a compact gate-free body distilling the SKILL.md flow
      (banner, read-only contract, critique discipline, exit map) with no
      `<!-- if: -->` markers, no `{refs}`, and no `<!-- include:preamble -->`
      (the duck drives no engine verbs). Re-run the suite from 2.1 and observe
      it pass.

## 3. Docs and packaging

- [x] 3.1 [req: duck-critic-session] Add a one-line `/s:duck` row to
      `README.md`'s command table (immediately before the `/s:plan` row) and
      to the `/s:` table in `docs/cheatsheet.md` (alphabetical — between
      `/s:doctor` and `/s:epic`), each mirroring its neighbors' style.
- [x] 3.2 [req: duck-critic-session] Add `/s:duck` to the AGENTS.md skill
      roster sentence in "Spec layout and lifecycle", phrased like its
      neighbors ("`/s:duck` to talk an idea through with the adversarial
      rubber-duck critic before planning it").
- [x] 3.3 [req: duck-critic-session] Bump the `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.156` to `0.6.157`.
- [x] 3.4 [req: *] Verification barrier: run the full engine suite `python3 -m
      unittest discover -s plugins/s/skills/build/tests` (without `textual` or
      `pydantic` installed) and confirm it passes; confirm `python3 -c
      "import sys; sys.path.insert(0, 'plugins/s/skills/build/scripts');
      import harness_bodies; print('duck' in harness_bodies.commands())"`
      prints `True`; confirm the `/s:duck` rows exist in `README.md`,
      `docs/cheatsheet.md`, and `AGENTS.md`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 102 | 37.2k |
| (no tool) | 0 | 23.9k |
| Read | 28 | 4.7k |
| Write | 3 | 4.3k |
| Agent | 6 | 4.2k |
| Edit | 7 | 3.7k |
| SendMessage | 4 | 2.4k |
| ToolSearch | 3 | 1.7k |
| **Total** | 153 | 82.3k |
