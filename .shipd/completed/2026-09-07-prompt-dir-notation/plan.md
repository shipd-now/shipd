# prompt-dir-notation
Status: verified

## Idea

Make every skill prompt adhere to the engine's content-directory resolver: a
canonical path-notation rule in the path-heavy prompts, targeted rewrites of
the load-bearing literal `.shipd/` lines, and an engine test that keeps the
convention true.

### Motivation

The content directory is configurable (the `dir` key, with nested values
arriving via the `content-dir-nested` change), but several skill prompts still
hardcode `.shipd/` — including runnable commands and layout-requirement
statements — so in a repo with a non-default directory the skills would read
and scan the wrong place. The user asked for the prompts to always adhere to
the binary resolver.

### Details

- Add one canonical notation sentence to `plugins/s/skills/build/SKILL.md`,
  `plugins/s/skills/epic/SKILL.md`, `plugins/s/skills/duck/SKILL.md`, and
  `plugins/s/skills/plan/references/emission.md`.
- Rewrite the load-bearing literals: runnable commands, constitution/README
  reads, the epic layout-requirement statement, one teach line.
- Add `plugins/s/skills/build/tests/test_prompt_notation.py` enforcing the
  convention line-by-line over `plugins/s/skills/**/*.md`.

Affected capabilities: `shipd-config` (added `skill-prompt-path-notation`).
Impact: the five prompt files above, the new test, and
`plugins/s/.claude-plugin/plugin.json`. No engine-script changes.

### Non-goals

- No engine-script changes — the resolver itself is `content-dir-nested`'s
  scope.
- No reword of every `.shipd/` mention: annotated mentions (a "default"-marked
  name, a `~/.shipd` home path, a `$SANDBOX` onboarding path) stay as they
  are, per the library's own `spec-library-path-notation` convention.
- `plugins/s/skills/onboard/SKILL.md` is exempt: its sandbox is created with
  the default layout, so its literals are intentionally exact.
- No change to fixed-path stores (`~/.shipd-memory`, `~/.shipd/designs`,
  `~/.shipd/rules`) or to the fixed `.shipd-config.json` filename.

## Implementation

- **The canonical notation sentence** (added verbatim to the four files named
  above, near each file's top): "Path notation: literal `.shipd/` paths in
  this skill denote the repo's resolved content directory (default `.shipd`) —
  resolve the actual name with `spec_status.py config-show` (its
  `content-dir:` line) and substitute it when the repo configures another."
  The test's marker substring is `denote the repo's resolved content
  directory`. Mirrors the master library's `spec-library-path-notation`
  requirement (see Q1 below); `worktree-hooks/SKILL.md` lines 61-66 already
  model the resolve-first pattern.
- **Enforcement contract** (the new test): for every line of every
  `plugins/s/skills/**/*.md` that contains `.shipd/`, the line passes when it
  contains `~/.shipd`, `$SANDBOX`, `default`, or `content directory`, or when
  its file is `plugins/s/skills/onboard/SKILL.md` or contains the marker
  substring; otherwise the test fails naming the file and line. Line-level
  exemptions keep already-correct prose (e.g. `initiative/SKILL.md:24`,
  `status/SKILL.md:22`) untouched. Stdlib-only, per the constitution.
- **Load-bearing rewrites** (each keeps its line passing the contract):
  - `build/SKILL.md:199-200`: replace `ls .shipd/verified/` /
    `ls .shipd/planned/` with resolving the directory first —
    `CONTENT_DIR=$(python3 ".../spec_status.py" config-show | sed -n
    's/^content-dir: //p')` then `ls "$CONTENT_DIR/verified/"` etc. Verified
    premise: `config-show` prints a `content-dir: .shipd` line (observed, exit
    0).
  - `build/SKILL.md:497`: pass `"$CONTENT_DIR/planned/<change-name>/tasks.md"`
    (resolved as above) instead of the hardcoded path.
  - `duck/SKILL.md:29`: read the report through the engine —
    `spec_status.py cat research ai-rubber-duck-dx` — instead of the literal
    path. Verified premise: the verb resolves and prints the report (observed
    from the repo root).
  - Constitution reads (`build/SKILL.md:88,297`, `duck/SKILL.md:65`,
    `plan/references/emission.md:30`): phrase as "the resolved content
    directory's `constitution.md` (default `.shipd/constitution.md`)".
  - `epic/SKILL.md:30`: reword the layout requirement to the resolver-aware
    phrasing `plan/SKILL.md:68` and `research/SKILL.md:40` already use.
  - `teach/SKILL.md:144`: "raw file reads of `.shipd/` internals" → "raw file
    reads of content-directory internals".
- **Build order**: build this change only after `content-dir-nested`
  (v0.6.185) merges — both bump `plugins/s/.claude-plugin/plugin.json`, so
  building in parallel collides on the version.
- Rejected alternative (Q1): rewording every `.shipd/` mention — abandons the
  shorthand the library deliberately standardized and inflates the diff.
- Risk: the line heuristic could flag legitimate future prose; guarded — the
  notation sentence in a file is a blanket pass, so any false positive costs
  one line.

## Questions and answers

### Q1: Notation rule or full reword?
- **Question:** To make skill prompts adhere to the configurable content
  directory, add a canonical notation rule to the path-heavy prompts plus
  targeted rewrites of load-bearing lines, or reword every `.shipd/` mention?
  Options: (a) notation rule + targeted fixes; (b) full reword.
  Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a). The master library resolves the identical problem by
  declaring that literal `.shipd/` prefixes denote the configured content
  directory rather than rewording every mention; mirroring that in the prompts
  keeps one convention across all surfaces and keeps the diff small.
- **Cited:** verified/shipd-config (`spec-library-path-notation`)

### Q2: Add an enforcement test for the notation convention?
- **Question:** Should the change add a stdlib-only engine test scanning every
  prompt line mentioning `.shipd/` (with exemptions), or ship prose-only?
  Options: (a) add the test; (b) prose-only. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Add the enforcement test — prompt-prose conventions erode
  without one; the answer is captured as standing knowledge so future prompt
  conventions ship with matching tests.
- **Queued:** q-prompt-dir-notation-enforcement-test
