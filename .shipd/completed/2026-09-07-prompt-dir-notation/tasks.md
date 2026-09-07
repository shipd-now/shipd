## 1. Enforcement test (test-first)

- [x] 1.1 [req: skill-prompt-path-notation] Add
      `plugins/s/skills/build/tests/test_prompt_notation.py` (stdlib-only):
      walk every `*.md` under `plugins/s/skills/`; for each line containing
      `.shipd/`, pass the line when it contains `~/.shipd`, `$SANDBOX`,
      `default`, or `content directory`, or when its file is
      `plugins/s/skills/onboard/SKILL.md` or contains the marker substring
      `denote the repo's resolved content directory`; otherwise collect
      `<path>:<lineno>` and fail with all offenders listed. Run it and
      observe it fail naming lines in `plugins/s/skills/build/SKILL.md`,
      `plugins/s/skills/epic/SKILL.md`, `plugins/s/skills/duck/SKILL.md`,
      `plugins/s/skills/teach/SKILL.md`, and
      `plugins/s/skills/plan/references/emission.md`.

## 2. Notation rule and load-bearing rewrites

- [x] 2.1 [req: skill-prompt-path-notation] Add the canonical notation
      sentence from `plan.md`'s `## Implementation` (verbatim, containing the
      marker substring) near the top of `plugins/s/skills/build/SKILL.md`,
      `plugins/s/skills/epic/SKILL.md`, `plugins/s/skills/duck/SKILL.md`, and
      `plugins/s/skills/plan/references/emission.md` (in each, directly after
      the file's opening requirements/context paragraph).
- [x] 2.2 [req: skill-prompt-path-notation] In
      `plugins/s/skills/build/SKILL.md`: replace the `ls .shipd/verified/` and
      `ls .shipd/planned/` commands (lines 199-200) with the resolve-first
      snippet from `plan.md`'s `## Implementation`; change line 497's
      hardcoded `.shipd/planned/<change-name>/tasks.md` argument to the
      resolved `"$CONTENT_DIR/planned/<change-name>/tasks.md"`; rephrase the
      constitution reads at lines 88 and 297 and the framing at lines 57-59 to
      the "resolved content directory (default `.shipd`)" phrasing.
- [x] 2.3 [req: skill-prompt-path-notation] Apply the remaining rewrites: in
      `plugins/s/skills/duck/SKILL.md` line 29 read the report via
      `spec_status.py cat research ai-rubber-duck-dx` and rephrase the
      constitution read at line 65; in `plugins/s/skills/epic/SKILL.md` line
      30 reword the layout requirement to the resolver-aware phrasing used at
      `plugins/s/skills/plan/SKILL.md` line 68; in
      `plugins/s/skills/plan/references/emission.md` line 30 rephrase the
      constitution read; in `plugins/s/skills/teach/SKILL.md` line 144 replace
      "raw file reads of `.shipd/` internals" with "raw file reads of
      content-directory internals".
- [x] 2.4 [req: skill-prompt-path-notation] Run
      `plugins/s/skills/build/tests/test_prompt_notation.py` and confirm it
      passes with zero offenders.

## 3. Ship hygiene

- [x] 3.1 [req: *] Run the full engine suite —
      `python3 -m unittest discover plugins/s/skills/build/tests` — and
      confirm it passes; set `version` in
      `plugins/s/.claude-plugin/plugin.json` to one greater than the version
      on current `main` (expected `0.6.186`, after `content-dir-nested`'s
      `0.6.185` has merged — build this change only after that PR lands).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 150 | 13.4k |
| Edit | 23 | 3.8k |
| (no tool) | 0 | 1.1k |
| Agent | 2 | 776 |
| Read | 10 | 389 |
| ToolSearch | 1 | 23 |
| Monitor | 1 | 17 |
| Write | 1 | 7 |
| **Total** | 188 | 19.6k |
