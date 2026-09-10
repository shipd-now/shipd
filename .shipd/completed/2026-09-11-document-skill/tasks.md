# document-skill — tasks

## 1. Lint engine (test-first)

- [x] 1.1 [req: document-lint-cli] Add
      `plugins/s/skills/document/tests/test_docs_lint.py` (unittest, stdlib
      only) covering: missing doc-type marker → error + exit 1; unknown
      doc-type value → error; concept doc over 100 lines → error; how-to
      over 150 and reference over 250 → error; conforming doc → exit 0, no
      output; 30-word descriptive sentence → error naming the 25-word cap;
      22-word sentence inside a numbered-list item → error naming the
      20-word procedural cap; paragraph of 7 sentences → error; two
      ```mermaid fences → error, one fence → no diagram finding; sentence
      with `e.g.` and an inline-code span like `spec_status.py` not split
      into false over-cap findings; passive-voice sentence ("the file was
      created") → warning line and exit 0 when it is the only finding;
      unreadable path → exit 2; finding format `file:line: error: message`.
      Mirror the test bootstrap style of
      `plugins/s/skills/review/tests/test_review_gate.py` (path insertion,
      tempfile fixtures). Run the suite and observe it fail — the script
      does not exist yet.
- [x] 1.2 [req: document-lint-cli] Implement
      `plugins/s/skills/document/scripts/docs_lint.py`, stdlib-only, per the
      plan's Lint mechanics decision: argv of one or more markdown paths;
      first-line `<!-- doc-type: concept|how-to|reference -->` marker
      required (error if missing/unknown); line caps 100/150/250 by type;
      prose analysis skips fenced code blocks, headings, tables (`|`-led
      lines), and the marker line; sentences split on `.`/`!`/`?` with
      abbreviation guard (`e.g.`, `i.e.`, `etc.`, `vs.`) and inline-code
      spans treated as single tokens; 25-word cap on descriptive sentences,
      20-word cap on sentences inside numbered-list items; contiguous prose
      block over 6 sentences → error; more than one ```mermaid fence →
      error; passive-voice heuristic (form of "be" then a word ending
      "-ed" or a common irregular participle within two words) → warning
      only, never affecting exit; findings as
      `file:line: error|warning: message`; exit 0 no errors / 1 any error /
      2 usage or IO. Run the 1.1 suite and make it pass.

## 2. Skill, registration, version

- [x] 2.1 [P2] [req: document-standard] Author
      `plugins/s/skills/document/references/standard.md` with exactly three
      level-2 sections. `## Core rules`: the seven STE-adapted rules from
      the plan's Implementation section with their exact numeric caps
      (active voice; 25-word descriptive / 20-word procedural sentence
      caps; one text category per sentence; 6-sentence paragraphs; specific
      verbs over make/do/take; 3-word noun clusters). `## Documentation
      rules`: the first-line `<!-- doc-type: ... -->` marker; the
      100/150/250 line caps by type; the mermaid structural test with the
      one-per-doc cap and no-restating rule; the shipd glossary with
      one-line definitions for change, worktree, epic, member, workspace,
      initiative, store, wiki, oracle, gate, capability, spec. `## Voice
      digest`: at most 12 lines distilling the core rules for
      conversational replies, written to stand alone when injected into a
      session with no other context. Then author
      `plugins/s/skills/document/SKILL.md`: YAML frontmatter matching house
      style (`name: document`; a `description:` in the style of
      `plugins/s/skills/duck/SKILL.md` with trigger phrases "document
      this", "write the docs", "rewrite this doc", "/s:document"). Body:
      point at `${CLAUDE_PLUGIN_ROOT}/skills/document/references/standard.md`
      as the single rules source (restate no numeric caps); the flow
      (classify each target doc as concept/how-to/reference →
      write/rewrite to the standard → run
      `python3 "${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/docs_lint.py" <files>`
      → fix until exit 0); a self-review checklist for the judgment rules
      (noun clusters, one word one meaning, diagram justification, active
      voice); and an explicit statement that the skill edits docs only and
      never commits, pushes, or opens a PR.
- [x] 2.2 [P2] [req: document-registration] In `.github/workflows/ci.yml`,
      add a step running
      `python3 -m unittest discover -s plugins/s/skills/document/tests -v`,
      matching the existing per-skill discover steps.
- [x] 2.3 [P2] [req: document-registration] Register the skill in prose: add
      an `/s:document` row to the `README.md` skill table (after the
      existing rows, style-matched); in `AGENTS.md`, add `/s:document` to
      the skill list sentence in "Spec layout and lifecycle" and add a short
      rule that documentation under `docs/` is authored and revised through
      `/s:document`, which carries the documentation standard and its lint.
- [x] 2.4 [P2] [req: document-voice-hook] Add
      `plugins/s/skills/document/tests/test_voice_digest.py` first
      (unittest, stdlib only; tempfile fixtures with a fake plugin root and
      config layers) covering: no `voice` key anywhere → digest body
      printed, exit 0; resolved `voice: false` → no output, exit 0;
      `standard.md` absent or missing its `## Voice digest` section → no
      output, exit 0. Observe it fail, then implement
      `plugins/s/skills/document/scripts/voice_digest.py` (stdlib-only,
      fail-soft: any internal error → print nothing, exit 0): resolve the
      layered configuration's `voice` key with the same upward search the
      engine uses (reuse `spec_common` config resolution via a
      `sys.path` insert of `skills/build/scripts`, guarded so an import
      failure exits 0 silently), default true; when enabled, print the
      `## Voice digest` section body of `references/standard.md`. Then add
      the `SessionStart` entry to `plugins/s/hooks/hooks.json` running
      `python3 "${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/voice_digest.py"`,
      preserving the existing PreToolUse/PostToolUse entries. Make the new
      tests pass.
- [x] 2.5 [req: document-registration] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.201` to `0.6.202`.

## 3. Integration fixes (test-covered surfaces the first pass missed)

- [x] 3.1 [req: guardrail-hook-registration] Update
      `plugins/s/skills/build/tests/test_guardrails.py`'s `HookRegistration`
      tests to the modified requirement: `hooks.json` declares exactly the
      three events `PreToolUse`, `PostToolUse`, `SessionStart` — the tool
      events unchanged (matcher `Edit|Write`, guardrails.py command), the
      `SessionStart` entry with the single command invoking
      `${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/voice_digest.py` via
      `python3`. Assert the SessionStart entry's shape too, not just the
      event list. Run the class and see it pass.
- [x] 3.2 [req: document-registration] Add the harness body template
      `plugins/s/harness/bodies/document.md`: first line a
      `<!-- description: <one line> -->` marker matching the skill's
      one-line purpose, then a compact command body in the house style of
      the existing `bodies/*.md` (read `bodies/duck.md` for shape): classify
      the target doc(s) as concept/how-to/reference, write or rewrite to
      the standard in `references/standard.md` (point at it, restate no
      caps), run `docs_lint.py`, fix findings until exit 0, edit docs only —
      never commit, push, or open a PR. Use no `<!-- if:... -->` gates so no
      fallback reference file is needed. Then run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm `test_harness_bodies` passes and no other test regressed.

## 4. Validator findings (one refuted scenario + config-key registration)

- [x] 4.1 [req: document-lint-cli] Fix the sentence-boundary defect in
      `plugins/s/skills/document/scripts/docs_lint.py`: delete the
      suppression that refuses a boundary when the next word starts
      lowercase — the spec authorizes exactly two guards (the abbreviation
      list and inline-code spans) and no third. A period followed by
      whitespace is a boundary unless a guard applies. While in the file,
      make the passive heuristic strip trailing punctuation from tokens so
      a sentence-final passive ("The spec is written.") still warns.
      Test-first in
      `plugins/s/skills/document/tests/test_docs_lint.py`: a conforming
      concept doc whose sentences open with the lowercase product name
      ("...build. shipd builds that change...") exits 0; a paragraph of
      seven short sentences each opening with "shipd" errors on the
      six-sentence cap; "The spec is written." warns; existing tests that
      encoded the lowercase suppression are updated to the two-guard rule.
      Run the document suite green.
- [x] 4.2 [req: voice-key] Register the `voice` key: add `voice` to the
      recognized-keys registry constant in
      `plugins/s/skills/build/scripts/spec_common.py`, and document it in
      `plugins/s/skills/build/references/shipd.config.example.json` as a
      `// voice` comment entry stating it gates the session-start voice
      digest and defaults to true (verbatim copy must still change no
      effective default). Update any build-suite test that enumerates the
      registry or the sample's keys. Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      the document suite; both green.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 191 | 59.3k |
| Write | 15 | 33.0k |
| Edit | 32 | 15.5k |
| (no tool) | 0 | 9.3k |
| AskUserQuestion | 3 | 3.8k |
| Read | 39 | 2.9k |
| Agent | 7 | 2.6k |
| ToolSearch | 4 | 645 |
| SendMessage | 1 | 461 |
| Monitor | 1 | 307 |
| **Total** | 293 | 127.9k |
