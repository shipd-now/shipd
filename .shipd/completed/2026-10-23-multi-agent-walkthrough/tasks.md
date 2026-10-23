## 1. Doc

- [x] 1.1 [req: multi-agent-walkthrough-doc] Write
      `docs/multi-agent-autonomous-prs.md` through `/s:document` per plan.md's
      outline. Check every command against `shipd room run --help`, and run
      `docs_lint.py` on it until it exits 0 within 150 lines.
- [x] 1.2 [req: multi-agent-walkthrough-doc] Add one `## See also` line
      linking the new page to `docs/multi-agent-pr.md` and to
      `docs/room-run.md`, keeping `room-run.md` within its 150-line cap.
      Re-run `docs_lint.py` on both.

## 2. Verify

- [x] 2.1 [req: *] Run `docs_lint.py` on all three files and
      `python3 -m unittest discover -s plugins/s/skills/document/tests`.
      Grep the output for `OK`/`FAILED`.
