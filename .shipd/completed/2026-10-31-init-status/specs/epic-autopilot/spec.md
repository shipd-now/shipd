## MODIFIED Requirements

### Requirement: Session turn result text
id: session-turn-result-text
base: 26431e01c989

The session driver SHALL provide `run_turn_result(prompt, cwd, resume_id=None,
timeout, harness="claude", binary=None, effort=None, model_base=None,
plugin_dir=None, extra_args=None, env=None)` returning `(ok, failure,
session_id, result_text)` where `result_text` is the headless turn's result
string as its harness runner extracts it, or an empty string when the
transcript carries no result text; `run_turn` SHALL accept the same `env`
argument and return the first three values unchanged for every existing
caller. `binary` SHALL default to the selected runner's own executable,
`effort` SHALL be the effort level or concrete model id the runner expresses,
and `model_base` SHALL be the base a harness that expresses a level as a model
variant appends it to. Where `env` is a mapping, the session subprocess SHALL
run with the current process environment overlaid by that mapping; where
`env` is `None`, the subprocess SHALL inherit the current environment
unchanged. A helper `result_text_from_transcript(text)` SHALL expose the
Claude transcript's extraction.

#### Scenario: The result text is returned
- **GIVEN** a binary that prints `{"session_id": "s1", "result":
  "{\"mode\": \"change\"}"}` and exits 0
- **WHEN** `run_turn_result` runs with the default harness
- **THEN** it returns `ok` true, session id `s1`, and the inner object text,
  while `run_turn` on the same binary returns `(True, None, "s1")`

#### Scenario: A non-JSON transcript yields an empty text
- **WHEN** `result_text_from_transcript("not json")` is called
- **THEN** it returns an empty string

#### Scenario: The env overlay reaches the session
- **GIVEN** a fake binary that prints a transcript whose `result` is the
  value of its `SHIPD_UNATTENDED` environment variable
- **WHEN** `run_turn_result` runs it with `env={"SHIPD_UNATTENDED": "1"}`,
  and again with no `env` from a process where the variable is unset
- **THEN** the first result text is `1` and the second is empty

## ADDED Requirements

### Requirement: Detached sessions run unattended
id: unattended-session-env

Every headless session the detached autopilot launches — each stage session
driven through its session seam and each drift-judge turn — SHALL run with
the environment variable `SHIPD_UNATTENDED` set to `1`, passed through the
session driver's `env` argument, so a skill inside the session that consults
`shipd init status` never opens its setup wizard. The autopilot SHALL NOT set
the variable in its own process environment, so its other subprocesses and
any eval or room runner sharing the session driver are unaffected.

#### Scenario: A stage session carries the flag
- **GIVEN** the production session seam with `session_driver.run_turn`
  replaced by a fake that records its keyword arguments
- **WHEN** the seam drives one stage session
- **THEN** the recorded `env` is `{"SHIPD_UNATTENDED": "1"}`

#### Scenario: A drift-judge turn carries the flag
- **GIVEN** the production judge seam with `session_driver.run_turn_result`
  replaced by a recording fake
- **WHEN** the seam runs one judge turn
- **THEN** the recorded `env` is `{"SHIPD_UNATTENDED": "1"}`

#### Scenario: The autopilot process itself stays clean
- **GIVEN** `SHIPD_UNATTENDED` is unset before the seams run
- **WHEN** both seams have run once
- **THEN** `SHIPD_UNATTENDED` is still absent from `os.environ`
