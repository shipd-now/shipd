## 1. The /s:explain skill

- [x] 1.1 [req: explain-epic-read] Create `plugins/s/skills/explain/SKILL.md`
      with frontmatter (`name: explain`, description with trigger phrases
      "explain this epic", "summarize the epic", "/s:explain"), the
      `shipd:explain v<version>` version banner read from
      `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`, and the read flow:
      run `spec_status.py cat epic <slug>` and `spec_status.py epic-show
      <slug>` from the repo root, engine-mediated only, with an explicit
      read-only contract (no Write/Edit, no mutating verbs, no artifacts) in
      the style of `plugins/s/skills/memory/SKILL.md` and
      `plugins/s/skills/duck/SKILL.md`.
- [x] 1.2 [req: explain-output-budget] In the same `SKILL.md`, add the output
      section: response text only, prose under 100 lines (diagram blocks
      excluded, cap not target), covering intent (Introduction + Decisions),
      member composition (Design + member table), and live delivery state
      (`epic-show` lanes and shipped count), in that order.
- [x] 1.3 [req: explain-diagram-policy] In the same `SKILL.md`, add the
      diagram policy section: include a diagram only when member dependency
      order, a pipeline, or actor hand-offs read faster as a picture;
      permitted forms are swimlane-style ASCII or a mermaid block; a simple
      epic gets no diagram.
- [x] 1.4 [req: explain-missing-epic] In the same `SKILL.md`, add the
      missing-epic fallback: on no argument or a `cat epic` non-zero exit,
      report the engine's error (when present), list the available epic slugs
      as the child directory names of `<content-dir>/epics/` (content dir from
      `spec_status.py config-show`), and stop without explaining.

## 2. Registration

- [x] 2.1 [req: *] Add `/s:explain` to the skill roster sentence in
      `AGENTS.md` (the `/s:` enumeration around line 118-130), phrased like
      its neighbors: "`/s:explain` to read a shipd epic and explain it in
      under 100 lines plus at-most-necessary diagrams".
- [x] 2.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.174` to `0.6.175`.

## 3. Harness body template

- [x] 3.1 [req: *] Create `plugins/s/harness/bodies/explain.md` per the
      verified `harness-command-bodies` capability: first line a
      `<!-- description: <one line> -->` marker, then a distilled router for
      `/s:explain` (read the epic via `spec_status.py cat epic <slug>` +
      `epic-show <slug>` through the preamble's `$S` scripts variable, the
      <100-prose-line explanation contract, the diagram policy, the
      missing-epic roster fallback), using `<!-- include:preamble -->`, **no
      `if:` gates** (so no `references/explain.md` is needed), no `{refs}`,
      and none of the tokens `subagent`, `sub-agent`, or `AskUserQuestion`;
      keep it under 120 lines and never copy more than 10 consecutive lines
      from `plugins/s/skills/explain/SKILL.md`. Model it on
      `plugins/s/harness/bodies/memory.md`.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests -p "test_harness_bodies*.py"` from the
      worktree root and confirm it passes, including
      `test_every_command_has_exactly_one_body_template`.

## 4. Verification

- [x] 4.1 [req: *] Re-read the finished `SKILL.md` against all four
      `shipd-explain` delta requirements and confirm the `AGENTS.md` roster
      line and the version bump are both in place; confirm no file outside
      the plan's named impact set changed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 95 | 18.6k |
| Edit | 11 | 3.9k |
| (no tool) | 0 | 3.6k |
| Read | 34 | 1.6k |
| Agent | 9 | 1.3k |
| ToolSearch | 1 | 23 |
| Write | 2 | 10 |
| **Total** | 152 | 29.0k |
