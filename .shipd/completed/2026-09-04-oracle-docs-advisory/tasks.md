## 1. Update the guide

- [x] 1.1 [req: oracle-user-docs] In `docs/oracle.md`, extend the `ANSWER`
      verdict section with the advisory variant: an example verdict carrying
      an `Authority: advisory` line after the position (source the semantics
      from the `shipd-ask` masters `oracle-cited-answers` and `ask-skill`,
      read via `spec_status.py cat verified shipd-ask`), stating that an
      advisory answer is a recommended, citable default the caller offers
      for the user to accept or override — never a silent settlement — and
      that an `ANSWER` without the line is binding as before.
- [x] 1.2 [req: oracle-user-docs] In `docs/oracle.md`, rewrite the
      capture-loop narrative (the paragraph after the ladder diagram and the
      "Using it directly" section) to describe classified capture per
      `plugins/s/skills/ask/references/capture-rubric.md`: the typed answer
      is classified include / exclude / consent-gated before any queue
      write; include captures via `wiki-queue-answer`; exclude discards the
      pending block via `wiki-queue-discard` (nothing stored); consent-gated
      records as advisory only on an express record-this instruction.
      Remove the claims that every answer is captured unconditionally.
- [x] 1.3 [req: oracle-user-docs] In `docs/oracle.md`, update the ladder's
      `mermaid` diagram so the capture path routes through the
      classification (rubric decides: answer, discard, or
      consent-gated advisory) instead of an unconditional
      `wiki-queue-answer` node, keeping it a single `mermaid` fence with no
      box-drawing characters.

## 2. Verify

- [x] 2.1 [req: *] Verification barrier: confirm `docs/oracle.md` satisfies
      every scenario of the modified `oracle-user-docs` requirement — grep
      shows `Authority: advisory`, the three tier names, and
      `wiki-queue-discard` present; the mermaid fence parses as one block;
      `grep -P '[\x{2500}-\x{257F}]' docs/oracle.md` finds no box-drawing
      characters — and run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` to
      confirm the docs-only change breaks nothing.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 43 | 11.7k |
| (no tool) | 0 | 2.6k |
| Read | 18 | 861 |
| Agent | 2 | 629 |
| Edit | 8 | 325 |
| ToolSearch | 1 | 3 |
| **Total** | 72 | 16.1k |
