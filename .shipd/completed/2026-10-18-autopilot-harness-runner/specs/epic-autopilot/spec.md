## MODIFIED Requirements

### Requirement: Shared session driver
id: shared-session-driver
base: 960a71884bad

The plugin SHALL ship a stdlib session-driver module exposing a grade-gated
resume loop: drive a headless session in a given working directory through a
**harness runner**, then, while a supplied grade function has not passed and
fewer than `max_resumes` resumed turns have run, resume the same session with a
supplied reply, returning success, the final session id, and any failure. The
runner SHALL be selected by harness id, so the loop is not tied to one
harness's CLI. If the working directory does not exist when a turn launches,
then the turn SHALL fail with a failure message naming the missing directory
rather than raising. The turn runner SHALL be injectable so the loop is testable
without live sessions, and the eval runner SHALL consume this module rather than
carrying its own copy of the loop.

#### Scenario: Loop stops when the grade passes
- **GIVEN** an injected runner whose second turn makes the grade pass
- **WHEN** the driver runs with max_resumes 4
- **THEN** exactly two turns run and the result is success

#### Scenario: Exhaustion surfaces the session id
- **GIVEN** an injected runner whose grade never passes
- **WHEN** the driver exhausts max_resumes
- **THEN** the result carries the session id for later interactive resume

#### Scenario: Missing working directory fails the turn, not the process
- **WHEN** a turn launches with a working directory that no longer exists
- **THEN** no exception propagates and the turn result is a failure whose
  message names the missing directory

#### Scenario: The loop is harness-agnostic
- **WHEN** a turn runs with `harness="opencode"` and a fake binary that prints
  an OpenCode JSONL transcript
- **THEN** the turn's session id and result text are read from that transcript,
  with the same loop and the same return contract as the `claude` runner

### Requirement: Session turn result text
id: session-turn-result-text
base: b53ee8e8158a

The session driver SHALL provide `run_turn_result(prompt, cwd, resume_id=None,
timeout, harness="claude", binary=None, model=None, plugin_dir=None,
extra_args=None)` returning `(ok,
failure, session_id, result_text)` where `result_text` is the headless turn's
result string as its harness runner extracts it, or an empty string when the
transcript carries no result text; `run_turn` SHALL return the first three
values unchanged for every existing caller. `binary` SHALL default to the
selected runner's own executable. A helper `result_text_from_transcript(text)`
SHALL expose the Claude transcript's extraction.

#### Scenario: The result text is returned
- **GIVEN** a binary that prints `{"session_id": "s1", "result":
  "{\"mode\": \"change\"}"}` and exits 0
- **WHEN** `run_turn_result` runs with the default harness
- **THEN** it returns `ok` true, session id `s1`, and the inner object text,
  while `run_turn` on the same binary returns `(True, None, "s1")`

#### Scenario: A non-JSON transcript yields an empty text
- **WHEN** `result_text_from_transcript("not json")` is called
- **THEN** it returns an empty string

## ADDED Requirements

### Requirement: Harness runners
id: harness-runners

The session driver SHALL declare a runner registry keyed by harness id, holding
at least `claude` and `opencode`. Each runner SHALL carry its default binary, an
`argv` builder, a transcript parser, and a prompt rewriter, and `runner_for(id)`
SHALL return the runner or raise a named error for an unknown id.

The `claude` runner SHALL build `[binary, "-p", prompt, "--output-format",
"json", "--plugin-dir", <plugin>, "--permission-mode", "bypassPermissions"]`
plus `--model <model>` and `--resume <id>`, parse the JSON object's `session_id`
and `result`, and rewrite no prompt text. The `opencode` runner SHALL build
`[binary, "run", "--format", "json", "--auto"]` plus `--model <model>` and
`--session <id>`, with the prompt as the trailing positional; parse the JSONL
stream's last top-level `sessionID` and the concatenated `part.text` of every
`type == "text"` line; and rewrite each `/s:<command>` token to
`/shipd-<command>`, the command name the harness installer writes.

#### Scenario: The claude runner keeps today's invocation
- **WHEN** the `claude` runner builds an argv with a model and a resume id
- **THEN** it is `[binary, "-p", <prompt>, "--output-format", "json",
  "--plugin-dir", <plugin>, "--permission-mode", "bypassPermissions",
  "--model", <model>, "--resume", <id>]`

#### Scenario: The opencode runner builds its invocation
- **WHEN** the `opencode` runner builds an argv with a model and a resume id
- **THEN** it is `[binary, "run", "--format", "json", "--auto", "--model",
  <model>, "--session", <id>, <prompt>]`

#### Scenario: The opencode runner parses its JSONL transcript
- **GIVEN** a transcript holding a `step_start` line and two `text` lines
  carrying `"hello"` and `" world"` under one `sessionID`
- **WHEN** the `opencode` runner parses it
- **THEN** the session id is that line's `sessionID` and the result text is
  `hello world`

#### Scenario: The opencode runner rewrites the command vocabulary
- **WHEN** the `opencode` runner rewrites `Run /s:plan for the change x`
- **THEN** the result names `/shipd-plan`, and the `claude` runner rewrites the
  same prompt unchanged

#### Scenario: An unknown harness is refused
- **WHEN** `runner_for("no-such-harness")` is called
- **THEN** it raises a named error naming the id
