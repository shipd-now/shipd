## 1. Engine verbs

- [x] 1.1 [req: wiki-queue-discard-verb, wiki-queue-answer-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add unittest cases
      (subprocess-against-temp-root style, matching the existing queue verb
      tests): `wiki-queue-discard <slug> --reason` removes a pending block,
      prints `q-<slug>`, exits 0, and preserves other blocks verbatim;
      discard of an answered block and of a missing block writes nothing and
      exits non-zero; `wiki-queue-answer --advisory` stores
      `- Answer: advisory: <text>`; a missing/empty `--reason` on discard
      exits non-zero. Run them and observe them fail — neither the verb nor
      the flag exists yet.
- [x] 1.2 [req: wiki-queue-discard-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, add
      `cmd_wiki_queue_discard(root, slug, reason)` next to
      `cmd_wiki_queue_answer`: same store resolution and bare-slug handling,
      require a non-empty `--reason`, remove the whole `## q-<slug>` block
      only when its `Answer:` is `pending` (refuse answered/missing with a
      non-zero exit naming the reason), print the `q-<slug>`; register the
      `wiki-queue-discard` subparser and dispatch.
- [x] 1.3 [req: wiki-queue-answer-verb] In the same file, add an
      `--advisory` store-true flag to the `wiki-queue-answer` subparser and
      prefix the stored answer with `advisory: ` when set.
- [x] 1.4 [req: wiki-autocommit] Auto-commit a successful discard via
      `sc.wiki_autocommit(wiki, [queue_path], "shipd-wiki: queue-discard
      q-<slug>")`, mirroring the answer verb; confirm the 1.1 tests now
      pass, then run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and fix
      any regression.

## 2. Rubric reference

- [x] 2.1 [req: capture-rubric] Copy this change's
      `artefacts/capture-rubric.md` verbatim to
      `plugins/s/skills/ask/references/capture-rubric.md` (create the
      `references/` directory).

## 3. Skill and agent surfaces

- [x] 3.1 [req: oracle-cited-answers] In `plugins/s/agents/oracle.md`, add
      the advisory-source rule to the verdict contract: an `ANSWER` whose
      backing source is a queue block with an `advisory: `-prefixed answer or
      a wiki page carrying an `Authority: advisory` line must itself carry an
      `Authority: advisory` line after the position; sources without the
      marker stay binding with no `Authority:` line.
- [x] 3.2 [req: ask-skill] In `plugins/s/skills/ask/SKILL.md`, add the
      advisory relay rule (an `Authority: advisory` `ANSWER` is put to the
      user with the oracle's position as the recommended first option,
      cited, never relayed as settled) and replace the unconditional capture
      step with rubric classification per
      `plugins/s/skills/ask/references/capture-rubric.md`: include → `wiki-queue-answer`;
      exclude → `wiki-queue-discard` with a one-line reason; consent-gated →
      one explicit record-this question, capture with `--advisory` only on
      an express yes, discard otherwise; failures reported, never blocking.
- [x] 3.3 [req: typed-answer-capture, oracle-consultation] In
      `plugins/s/skills/plan/SKILL.md`, update "The oracle rung" (advisory
      `ANSWER` enters the typed round as the recommended default with its
      citation instead of folding in) and the "Capture the typed resolution"
      step (classify per the rubric at
      `plugins/s/skills/ask/references/capture-rubric.md`; include captures,
      exclude discards via `wiki-queue-discard`, consent-gated captures
      `--advisory` only on express affirmation; ledger entries unchanged for
      every tier).
- [x] 3.4 [req: ask-skill] Mirror the 3.2 classification, consent, and
      advisory-relay rules in `plugins/s/harness/bodies/ask.md` (steps 4–5)
      and `plugins/s/harness/references/ask.md`, keeping the two renderings
      consistent with the skill.
- [x] 3.5 [req: teach-queue-drain] In `plugins/s/skills/teach/SKILL.md`
      step 5, direct the drain to detect the `advisory: ` answer prefix and
      write the distilled page with an `Authority: advisory` line, leaving
      unprefixed answers distilling as binding pages.

## 4. Ship

- [x] 4.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to `0.6.175`.
- [x] 4.2 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` and
      confirm the full suite passes with no `textual` installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 150 | 33.0k |
| Edit | 30 | 7.3k |
| (no tool) | 0 | 6.2k |
| Read | 141 | 5.6k |
| Agent | 11 | 2.3k |
| Write | 6 | 889 |
| Monitor | 3 | 36 |
| ToolSearch | 1 | 2 |
| **Total** | 342 | 55.3k |
