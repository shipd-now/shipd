## 1. The skill

- [x] 1.1 [req: doctor-skill-flow, doctor-remedy-boundaries] Author
      `plugins/s/skills/doctor/SKILL.md`: frontmatter (`name: doctor`,
      description with the `/s:doctor` trigger and "fix my setup" /
      "check my environment" phrases); the flow — resolve the binary
      (`shipd` on PATH, else `${CLAUDE_PLUGIN_ROOT}/bin/shipd`), run
      `shipd doctor`, parse the `ok|warn|fail <check> — <detail>` lines,
      stop on all-ok, otherwise one consent dialog over the runnable
      remedies (dialog-prose separation honored), run only consented
      remedies, re-run doctor, report before/after, one remedy round max,
      unparseable output reported as a failure; the remedy table with its
      safety boundaries (`gh auth login` handed off as `! gh auth login`;
      `python`/`config` report-only; textual range
      `"textual>=8.2.8,<9"`; `claude plugin update s@shipd` with the
      restart note; platform command stated before running for gh/git).
- [x] 1.2 [req: doctor-skill-registration] Include the question-rejection
      recovery rule verbatim in `plugins/s/skills/doctor/SKILL.md`,
      matching the other interactive skills' wording.

## 2. Registration and mirrors

- [x] 2.1 [req: doctor-skill-registration] Add the `/s:doctor` row to
      `README.md`'s skills table and the doctor skill to `AGENTS.md`'s
      skill enumeration, descriptions consistent with the frontmatter.
- [x] 2.2 [req: doctor-remedy-boundaries] Add a one-line comment to
      `requirements.txt` noting the textual range is mirrored in
      `plugins/s/skills/doctor/SKILL.md`.

## 3. Ship

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Run `plugins/s/skills/build/tests/` (no `textual`) as a
      regression pass — this change adds no code, the suite must stay
      green.
