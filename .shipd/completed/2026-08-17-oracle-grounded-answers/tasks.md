## 1. Engine verb

- [x] 1.1 [req: wiki-queue-answer-verb, wiki-autocommit] Add tests to
      `plugins/s/skills/build/tests/test_spec_status.py` for
      `wiki-queue-answer`: a pending block's `- Answer: pending` line is
      replaced with the given text, the slug is printed, exit 0, and (store in
      a git work tree with identity) a commit lands containing only
      `queue.md`; a missing block exits non-zero writing nothing; a
      non-`pending` block exits non-zero writing nothing; a `--root` with no
      discoverable workspace exits non-zero with the no-workspace error. Run
      the tests and observe them fail — the verb does not exist yet.
- [x] 1.2 [req: wiki-queue-answer-verb] Implement the `wiki-queue-answer`
      verb in `plugins/s/skills/build/scripts/spec_status.py` beside
      `wiki-queue-add` (parser registration near line 2698, dispatch near
      line 2769), stdlib-only, resolving the store exactly as
      `wiki-queue-add` does and accepting the bare slug (prefix `q-`
      internally).
- [x] 1.3 [req: wiki-autocommit] Route the successful `wiki-queue-answer`
      write through the same scoped auto-commit helper `wiki-queue-add` uses,
      committing only `queue.md`; confirm every test from 1.1 now passes.

## 2. Stricter oracle

- [x] 2.1 [P1] [req: oracle-agent-contract, oracle-cited-answers] Edit
      `plugins/s/agents/oracle.md`: state the default-`INSUFFICIENT`
      grounding bar (never answer from model knowledge; `ANSWER` only when a
      cited source states a position on the specific decision); require at
      least one verbatim `Evidence:` quote line under every `ANSWER`; add the
      answered-queue read to the job-store rung after the pages (`cat wiki
      queue`, blocks whose `Answer:` is not `pending`, cited as
      `Cited: queue q-<slug>`); update the worked `ANSWER` example to show an
      `Evidence:` line.

## 3. Interactive callers

- [x] 3.1 [P1] [req: ask-skill] Edit `plugins/s/skills/ask/SKILL.md`: demote an
      `ANSWER` verdict missing `Cited:` or `Evidence:` to `INSUFFICIENT`; on
      `INSUFFICIENT`, put the compact question to the user through one
      AskUserQuestion dialog (recommendation listed first), distill the reply
      into a concise durable answer, write it via `spec_status.py
      wiki-queue-answer` against the verdict's filed `q-<slug>`, and on
      `Queued: none` relay the answer for the session only, stating nothing
      durable was captured.
- [x] 3.2 [P1] [req: oracle-consultation, typed-answer-capture] Edit
      `plugins/s/skills/plan/SKILL.md`'s "The ask-mikk rung" section: add the
      malformed-`ANSWER` demotion rule (missing `Cited:`/`Evidence:` treated
      as `INSUFFICIENT`), and add the post-round capture step — after a typed
      round resolves an `INSUFFICIENT` decision whose verdict filed a
      `q-<slug>`, distill the typed resolution and write it via
      `wiki-queue-answer` before emission; skip with a visible note on
      `Queued: none`; a failed write is reported and never blocks planning.

## 4. Documentation and release

- [x] 4.1 [P1] [req: oracle-user-docs] Add `docs/oracle.md` in the voice of the
      existing `docs/` guides: what the ask-mikk oracle is, an ASCII diagram
      of the read → ask-mikk → human ladder including the
      ask-the-user-then-capture loop, one worked `ANSWER` example (with
      `Cited:` and `Evidence:` lines) and one `INSUFFICIENT` example (with
      its queued question), the definitive-evidence bar, and the correction
      path via `/s:teach`.
- [x] 4.2 [P1] [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to `0.6.125`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 84 | 32.6k |
| Edit | 21 | 11.9k |
| Read | 7 | 3.0k |
| (no tool) | 0 | 1.1k |
| Agent | 1 | 370 |
| **Total** | 113 | 49.0k |
