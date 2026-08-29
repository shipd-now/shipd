## 1. Plugin prose sweep

- [x] 1.1 [req: *] In `plugins/s/agents/oracle.md`, `plugins/s/harness/bodies/ask.md`,
      and `plugins/s/harness/bodies/remember.md`, replace every "ask-mikk
      oracle" with "the oracle", "read → ask-mikk → human" with
      "read → oracle → human", and "mikk's standing opinion/position" and
      "mikk's opinion" with the user's-standing equivalents ("the user's
      standing opinion", "the user's opinion").
- [x] 1.2 [req: *] In `plugins/s/skills/ask/SKILL.md`, apply the same
      replacements, including the frontmatter description and trigger
      phrases: "ask mikk" → "ask the oracle", "consult mikk" → "consult the
      oracle", "get mikk's standing opinion" → "get the user's standing
      opinion".
- [x] 1.3 [req: *] In `plugins/s/skills/plan/SKILL.md`, rename the section
      "The ask-mikk rung — consult the oracle before the user" to "The
      oracle rung — consult the oracle before the user" and sweep every
      "ask-mikk"/"mikk" token in the body ("the ask-mikk rung" → "the oracle
      rung", "mikk's captured preferences" → "the user's captured
      preferences", "mikk's standing opinion" → "the user's standing
      opinion").
- [x] 1.4 [req: *] In `plugins/s/skills/plan/references/readiness.md` and
      `plugins/s/skills/plan/references/dialogue.md`, update the verbatim
      references to the renamed "The ask-mikk rung" section and sweep
      "ask-mikk oracle"/"mikk's standing answer" tokens; in
      `plugins/s/skills/plan/references/emission.md`, sweep "ask-mikk
      oracle" and change the design-path example `/home/mikk/...` to
      `/home/user/...`.
- [x] 1.5 [req: *] In `plugins/s/skills/teach/SKILL.md`,
      `plugins/s/skills/memory/SKILL.md`, `plugins/s/skills/remember/SKILL.md`,
      and `plugins/s/skills/autopilot/SKILL.md`, sweep "teach mikk" → "teach
      the oracle", "Teach mikk:" → "Teach the oracle:", "mikk's durable
      memories" → "the user's durable memories", "mikk prefers" → "the user
      prefers", "ask-mikk oracle" → "the oracle", and "ask-mikk
      consultation" → "oracle consultation".
      Leave the epic/mikk-knowledge example citation in
      `plugins/s/skills/teach/SKILL.md` unchanged.
- [x] 1.6 [req: *] In `plugins/s/skills/build/scripts/autopilot.py`, sweep
      the three "ask-mikk oracle" prompt strings to "the oracle"; update the
      matching docstring mention in
      `plugins/s/skills/build/tests/test_autopilot.py`. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -q` and
      confirm it passes.
- [x] 1.7 [req: *] In `plugins/s/skills/review/SKILL.md`, replace both
      "CodeRabbit-style" phrases with "in the style of popular code-review
      tools" phrasing (frontmatter description and body line), keeping the
      rest of each sentence intact.

## 2. Test fixtures

- [x] 2.1 [req: *] In `plugins/s/skills/build/tests/test_spec_lint.py`,
      `test_spec_status.py`, and `test_spec_emit.py`, rename the video-brief
      fixture speaker "Mikk — product lead" to "Ada — product lead" and every
      transcript/source line speaker "Mikk:" to "Ada:", updating in the same
      edit each assertion that quotes those strings (e.g. the
      `has(errors, "Mikk: ...")` check).
- [x] 2.2 [req: *] In `plugins/s/skills/build/tests/test_spec_common.py`,
      `test_spec_lint.py`, and `test_spec_status.py`, rename the queue-block
      origin fixture `teach-mikk` (as in `- Asked: 2026-07-30 teach-mikk` and
      the `--origin teach-mikk` round-trip with its `assertIn`) to
      `teach-session`.
- [x] 2.3 [req: *] In `plugins/s/skills/build/tests/test_tui_bootstrap.py`,
      change the fixture `HOME` value `/home/mikk` to `/home/user` in all
      three occurrences. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -q` and
      confirm it passes.

## 3. Docs and repo files

- [x] 3.1 [req: *] Rewrite `docs/oracle.md`: title "# The ask-mikk oracle" →
      "# The oracle", and sweep every "ask-mikk"/"mikk" token in the body
      (ladder "read → oracle → human", "the user's standing opinion").
- [x] 3.2 [req: readme-displays-the-shipd-banner] In `README.md`, update the
      `/s:ask` row ("ask-mikk oracle" → "the oracle") and the `/s:review`
      row ("CodeRabbit-style" → "in the style of popular code-review
      tools"), keeping each row consistent with the skill's updated
      frontmatter description; apply the same "ask-mikk oracle" → "the
      oracle" fix to `docs/cheatsheet.md`'s `/s:ask` row and `AGENTS.md`'s
      skill list sentence.
- [x] 3.3 [req: *] In `.shipd/README.md`, change "the ask-mikk oracle
      consultations" to "the oracle consultations".

## 4. Verified spec wording sweep

- [x] 4.1 [req: *] In `.shipd/verified/shipd-ask/spec.md` (the "ask-mikk
      oracle ... read → ask-mikk → human ladder" requirement text) and
      `.shipd/verified/epic-autopilot/spec.md` (both "ask-mikk oracle"
      mentions), apply the boundary-anchored rewrites to "the oracle" /
      "read → oracle → human" — wording only, no id or scenario structure
      changes. Leave `.shipd/verified/project-readme/spec.md` untouched (its
      id is renamed by this change's delta at merge) and leave
      `.shipd/verified/shipd-teach/spec.md`'s epic/mikk-knowledge citation
      unchanged. Run
      `python3 plugins/s/skills/build/scripts/spec_lint.py --root .` and
      confirm no findings for the library.

## 5. Version bump and completion gate

- [x] 5.1 [req: *] Read the current version in
      `plugins/s/.claude-plugin/plugin.json` (0.6.154 at planning) and bump
      one patch level.
- [x] 5.2 [req: *] Run the residual scan
      `grep -rniE "mikk|coderabbit" plugins/s docs README.md AGENTS.md tools install.sh action.yml .shipd/verified .shipd/README.md evals --exclude-dir=__pycache__`
      and confirm every hit is on the allowlist recorded in `plan.md`'s
      residual-scan decision (`tools/port.py` + its tests' automikk mapping
      tokens; the `~/.automikk/` guards in `build_report.py` + its tests;
      the epic/mikk-knowledge citations in
      `.shipd/verified/shipd-teach/spec.md` and
      `plugins/s/skills/teach/SKILL.md`; "Mikkel Bergmann" /
      `mikkelbergmann` / `mikkel-bergmann` author, account, and path
      tokens). Fix any other survivor.
- [x] 5.3 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests -q` and
      `python3 -m unittest discover -s plugins/s/skills/review/tests -q`
      and confirm both pass.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 108 | 13.9k |
| Edit | 16 | 3.8k |
| Agent | 2 | 1.4k |
| (no tool) | 0 | 1.0k |
| Read | 6 | 231 |
| **Total** | 132 | 20.3k |
