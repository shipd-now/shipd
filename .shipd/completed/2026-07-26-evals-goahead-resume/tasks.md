## 1. Conversation loop in the runner

- [x] 1.1 [req: headless-skill-run] In `evals/tests/test_runner.py`, add
      unit tests for the conversation loop, driven by an injected fake turn
      runner (no live session): the loop resumes with the generic reply and
      passes once a fake turn writes a gradable change; the resume cap
      bounds the number of turns and the run fails with the structural
      grading failure when exhausted; a failing turn (ok=False) fails the
      run immediately; a missing session id stops resuming. Also test
      `_session_id_from_transcript` on valid JSON, JSON without the field,
      and non-JSON text. Run them and observe them fail — the loop does not
      exist yet.
- [x] 1.2 [req: headless-skill-run] In `evals/run.py`, implement the loop:
      `_session_id_from_transcript(text)` (pure helper); `_run_turn(...)`
      spawning `claude -p <prompt> [--resume <id>] --plugin-dir ...
      --permission-mode bypassPermissions --output-format json` and writing
      `eval-transcript.json` (turn 1) / `eval-transcript-turn<N>.json`
      (later turns); `run_conversation(case, scratch, ..., max_resumes=4,
      turn_runner=_run_turn)` sending the case prompt then the generic
      accept-recommendations reply (module constant) while
      `grade(scratch)` has not passed; a `--max-resumes` CLI flag wired
      through `execute_case`. Confirm the 1.1 tests pass.
- [x] 1.3 [req: headless-skill-run] Run both unit suites and observe them
      pass: `uvx pytest evals/tests/ -q` and `python3 -m unittest discover
      -s plugins/s/skills/build/tests`.
- [x] 1.4 [req: headless-skill-run] Live verification: `python3
      evals/run.py --case plan-csv-export --keep-scratch` passes (real
      session spend), with the kept scratch showing at least one resumed
      turn transcript.

## 2. Docs

- [x] 2.1 [req: headless-skill-run] In `AGENTS.md`'s Evals section, note
      the runner drives each session through the plan skill's checkpoint
      and decision rounds by resuming with the session's own recommended
      options (bounded by `--max-resumes`).
