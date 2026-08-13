# evals-goahead-resume
Status: verified

## Idea

The eval harness is single-shot: one `claude -p` invocation, then structural
grading. Since the plan skill gained its findings checkpoint (0.2.12) and
typed decision rounds (0.2.14), a real `/s:plan` session *requires* user
replies — the headless session correctly stops at the checkpoint (digest +
go-ahead prompt, or an OPEN QUESTIONS ending as of 0.3.2), nobody answers,
and no change is ever emitted. Both plan cases now fail with "no change
directory under `.shipd/planned/`", so the AGENTS.md convention that SKILL.md
changes get an eval run is unenforceable.

Fix: the runner drives the session as a bounded conversation. After the
initial turn it grades the scratch repo; while the grade has not passed and a
resume cap is not exhausted, it resumes the same session (`--resume
<session_id>`, parsed from the previous turn's JSON transcript) with a fixed
generic reply that proceeds and takes the session's recommended option on any
open question or decision, then re-grades. Turn transcripts are all kept in
the scratch directory.

### Non-goals

- No change to grading (still exactly-one lint-clean change at
  `Status: ready`), discovery, pass-rate reporting, or the cases/fixtures.
- No per-case scripted dialogues: one generic accept-recommendations reply is
  the contract; a case needing bespoke answers is future work.
- No plugin changes — `plugins/s/` is untouched, so no version bump.

Affected capabilities: `skill-evals` (modified — `headless-skill-run`).
Impact: `evals/run.py`, `evals/tests/test_runner.py`, `AGENTS.md`.

## Implementation

- **Conversation loop in `run.py`.** `run_conversation(case, scratch, ...)`
  replaces the single `run_session` call: turn 1 sends the case prompt; then
  up to `--max-resumes` times (default 4): if `grade(scratch)` passes, stop;
  otherwise resume with the generic reply. A turn that times out or exits
  non-zero fails the run immediately, as today. If a turn's transcript
  yields no `session_id`, the loop stops and the final grade decides —
  the structural failure is the more informative report.
- **Turn runner is injectable.** The subprocess-spawning `_run_turn` is a
  default parameter of `run_conversation`, so unit tests drive the loop with
  fakes (pass-after-first-resume, cap exhaustion, missing session id)
  without live sessions — matching the harness's existing tested/untested
  split. `_session_id_from_transcript(text)` is a pure helper, also tested.
- **The generic reply** (a module constant): proceed; for any open question
  or decision now or later, take the option you yourself recommend; drive
  the plan through emission, lint, and promotion to ready. This answers the
  go-ahead prompt, an OPEN QUESTIONS ending, and typed decision rounds
  alike, without biasing any specific design choice.
- **Transcripts per turn.** Turn 1 keeps `eval-transcript.json`; resumed
  turns write `eval-transcript-turn<N>.json` alongside it.
- **Docs.** AGENTS.md's eval paragraph gains half a sentence: the runner
  drives the session through its checkpoint and decision rounds by resuming
  with the recommended options.

Risks: a session that can never satisfy the grader burns the resume cap
(bounded, ~4 extra turns of spend per failing run); the cap is a CLI flag so
a cheap `--max-resumes 0` restores single-shot behavior for debugging. The
resume flags (`--resume` with `-p`) are standard Claude Code CLI; if resume
fails the turn exits non-zero and the run fails with that error named.
