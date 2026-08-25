## ADDED Requirements

### Requirement: Rulebook file format
id: guardrail-rulebook-format

A guardrail rule SHALL be a markdown file `<name>.md` whose rule name is the
filename stem. The file SHALL open with a frontmatter block delimited by
`---` lines, parsed as flat `key: value` pairs (split on the first colon;
unknown keys ignored): `pattern` (required, Python `re` syntax applied per
added line with `re.search`), `mode` (`deny` when absent, or `remind`),
`files` (optional comma-separated `fnmatch` globs), and `cooldown` (optional
positive integer seconds, meaningful only with `mode: remind`). The content
after the frontmatter SHALL be the rule's corrective message and MUST be
non-empty after stripping. If a file lacks a `pattern`, has an empty message
body, declares an unrecognized `mode`, or its pattern does not compile, then
the loader SHALL skip that file and keep loading the rest.

#### Scenario: A valid rule file loads
- **GIVEN** `no-console-log.md` with frontmatter `pattern: console\.log\(`
  and a body message
- **WHEN** the rulebook is loaded
- **THEN** a deny rule named `no-console-log` with that pattern and message
  is in the registry

#### Scenario: A remind rule parses its mode and cooldown
- **GIVEN** a rule file with `mode: remind` and `cooldown: 300`
- **WHEN** the rulebook is loaded
- **THEN** the rule carries mode `remind` and a 300-second cooldown

#### Scenario: A file without a pattern is skipped
- **GIVEN** a rules directory holding one file with no `pattern` key and one
  valid rule file
- **WHEN** the rulebook is loaded
- **THEN** only the valid rule is in the registry

#### Scenario: An unrecognized mode is skipped
- **GIVEN** a rule file declaring `mode: interrupt`
- **WHEN** the rulebook is loaded
- **THEN** that rule is not in the registry

### Requirement: Rulebook discovery and precedence
id: guardrail-rulebook-discovery

The hook SHALL build its registry from three sources, deduplicated by rule
name with the first-listed source winning: (1) each ancestor directory of the
payload `cwd` (falling back to the process cwd), walked parent-by-parent to
the filesystem root, contributing `<content-dir>/rules/*.md` where
`<content-dir>` is the resolved configuration's `dir` value — nearer
ancestors first; (2) `~/.shipd/rules/*.md`; (3) the plugin's own
`hooks/rules/*.md` built-ins, resolved relative to the script's own file
location. Names listed in the resolved config's `guardrails.disable` SHALL be
dropped after the merge, and `guardrails: false` SHALL disable every source.

#### Scenario: A repo rule overrides a built-in by name
- **GIVEN** `<repo>/.shipd/rules/changelog-comment.md` declaring a different
  pattern and message
- **WHEN** the rulebook is loaded from that repo
- **THEN** the registry holds one `changelog-comment` rule carrying the repo
  file's pattern

#### Scenario: A user rule applies in every repo
- **GIVEN** `~/.shipd/rules/no-console-log.md` and a repo with no rules
  directory
- **WHEN** an Edit in that repo adds `console.log(user)`
- **THEN** the call is denied citing `no-console-log`

#### Scenario: Disable drops a built-in file rule
- **GIVEN** a config layer declaring
  `"guardrails": {"disable": ["narrating-comment"]}`
- **WHEN** an Edit adds a line matching only `narrating-comment`
- **THEN** the call is allowed while the other built-ins stay active

### Requirement: Remind mode output
id: guardrail-remind-output

When invoked with a payload whose `hook_event_name` is `PostToolUse`, the
script SHALL evaluate only `mode: remind` rules against the added lines, and
when at least one applicable rule fires outside its cooldown, SHALL print
`{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": <text>}}`
to stdout and exit 0, where the text names each firing rule and its message.
When the event is `PreToolUse` (or the field is absent), the script SHALL
evaluate only `deny` rules. A remind rule SHALL fire at most once per session
per rule by default — keyed by the payload `session_id`, with state persisted
under `~/.shipd/guardrails/` — and a rule declaring `cooldown: <seconds>`
SHALL fire again once that many seconds have passed since its last fire in
the session. If the payload carries no `session_id`, then the rule SHALL fire
without recording state. When no remind rule fires, the script SHALL exit 0
printing nothing.

#### Scenario: A remind rule injects context without blocking
- **GIVEN** a repo rule file with `mode: remind` matching `console\.log\(`
- **WHEN** a PostToolUse payload's Edit added `console.log(user)`
- **THEN** stdout carries `additionalContext` naming the rule and its
  message, and the exit code is 0

#### Scenario: The same rule is silent for the rest of the session
- **GIVEN** a remind rule with no `cooldown` that already fired for this
  `session_id`
- **WHEN** a second matching PostToolUse payload arrives with the same
  `session_id`
- **THEN** the script exits 0 printing nothing

#### Scenario: A deny rule is not evaluated on PostToolUse
- **GIVEN** only the built-in deny rules
- **WHEN** a PostToolUse payload's Edit added `// Fixed: off-by-one`
- **THEN** the script exits 0 printing nothing

#### Scenario: A remind rule is not denied on PreToolUse
- **GIVEN** a repo rule file with `mode: remind` matching `console\.log\(`
- **WHEN** a PreToolUse payload's Edit adds `console.log(user)`
- **THEN** the call is not denied on that rule's account

## MODIFIED Requirements

### Requirement: Hook registration in the plugin
id: guardrail-hook-registration
base: c020b453cee3

The plugin SHALL ship a `hooks/hooks.json` at the plugin root that registers
exactly two events: a `PreToolUse` hook and a `PostToolUse` hook, each with
matcher `Edit|Write` and each with the single command entry
`{"type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/guardrails.py\""}`.

#### Scenario: hooks.json declares both events
- **WHEN** `plugins/s/hooks/hooks.json` is parsed as JSON
- **THEN** it declares exactly the events `PreToolUse` and `PostToolUse`,
  each with matcher `Edit|Write` and a command invoking
  `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/guardrails.py` via `python3`

### Requirement: Built-in default rules
id: guardrail-default-rules
base: b02d366c5bd2

The plugin SHALL ship exactly three built-in rules as rule files under its
`hooks/rules/` directory — `changelog-comment.md` with pattern
`(?i)(?:#|//)\s*(?:added|updated|changed|fixed|new|refactored)\s*:`,
`narrating-comment.md` with pattern
`(?i)(?:#|//)\s*(?:now|then|next|first|finally),?\s+(?:we|i|it)\s`, and
`filler-placeholder.md` with pattern
`(?i)(?:#|//)\s*(?:\.\.\.\s*)?(?:rest of |existing code|remains? unchanged|unchanged below|no changes? (?:here|needed))`
— each `mode: deny` with its corrective message as the file body, active by
default in every repository. The script SHALL carry no in-code rule content.

#### Scenario: A change-log comment is denied by default
- **GIVEN** no `.shipd-config.json` layer declaring `guardrails` and no repo
  or user rule files
- **WHEN** an Edit adds the line `// Fixed: off-by-one in pager`
- **THEN** the call is denied citing `changelog-comment`

#### Scenario: A narration comment is denied by default
- **WHEN** an Edit adds the line `# now we build the index`
- **THEN** the call is denied citing `narrating-comment`

#### Scenario: A placeholder comment is denied by default
- **WHEN** a Write's content contains the line `// ... rest of the file`
- **THEN** the call is denied citing `filler-placeholder`

#### Scenario: The built-ins are ordinary rule files
- **WHEN** `plugins/s/hooks/rules/` is listed
- **THEN** it holds exactly `changelog-comment.md`, `narrating-comment.md`,
  and `filler-placeholder.md`, each parseable by the rulebook format

### Requirement: Fail-open behavior
id: guardrail-fail-open
base: a0706723846a

If stdin is not parseable JSON, the resolved `guardrails` config value is
malformed, a rule file is unreadable or malformed, a rule's pattern does not
compile, cooldown-state I/O fails, or any unexpected exception is raised,
then the script SHALL exit 0 without denying, skipping only the affected rule
or state operation while the rest of the evaluation proceeds where possible.
Where the environment variable `SHIPD_GUARDRAILS` equals `off`, the script
SHALL exit 0 immediately with no output. The script SHALL never exit
non-zero.

#### Scenario: Garbage stdin passes through
- **WHEN** the script receives non-JSON stdin
- **THEN** it exits 0 and prints nothing

#### Scenario: The env bypass disables everything
- **GIVEN** `SHIPD_GUARDRAILS=off` in the environment
- **WHEN** a payload that would otherwise be denied is evaluated
- **THEN** the script exits 0 and prints nothing

#### Scenario: A malformed rule file is skipped
- **GIVEN** a repo rules directory holding one unparseable rule file
- **WHEN** a payload matching a built-in rule is evaluated
- **THEN** the built-in still denies and the script exits 0

#### Scenario: An unwritable state directory still reminds
- **GIVEN** a remind rule firing while the cooldown-state directory cannot be
  written
- **WHEN** the PostToolUse evaluation runs
- **THEN** the reminder is still emitted and the script exits 0

