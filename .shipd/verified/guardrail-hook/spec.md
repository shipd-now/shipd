# guardrail-hook

### Requirement: Hook registration in the plugin
id: guardrail-hook-registration

The plugin SHALL ship a `hooks/hooks.json` at the plugin root that registers
one `PreToolUse` hook with matcher `Edit|Write` whose single command entry is
`{"type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/guardrails.py\""}`,
and SHALL register no other hook events.

#### Scenario: hooks.json declares the PreToolUse hook
- **WHEN** `plugins/s/hooks/hooks.json` is parsed as JSON
- **THEN** it declares exactly one event, `PreToolUse`, with matcher
  `Edit|Write` and a command invoking
  `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/guardrails.py` via `python3`

### Requirement: Added-line extraction
id: guardrail-added-line-matching

When invoked with a PreToolUse payload whose `tool_name` is `Edit`, the
guardrail script SHALL evaluate rules against only the lines of
`tool_input.new_string` that are not present, as exact line matches, among the
lines of `tool_input.old_string`. When `tool_name` is `Write`, it SHALL
evaluate rules against every line of `tool_input.content`. If `tool_name` is
any other value, then the script SHALL exit 0 with no output.

#### Scenario: A moved line is not re-flagged
- **GIVEN** an Edit whose `old_string` and `new_string` both contain the line
  `# fixed: legacy comment`
- **WHEN** the guardrail script evaluates the payload
- **THEN** that line is not treated as added and no rule is evaluated against
  it

#### Scenario: A Write scans the whole content
- **WHEN** a Write payload's `content` contains a line matching an enabled rule
- **THEN** the script denies the call

#### Scenario: Other tools pass through
- **GIVEN** a payload with `tool_name` `NotebookEdit`
- **WHEN** the guardrail script runs
- **THEN** it exits 0 and prints nothing

### Requirement: Deny output contract
id: guardrail-deny-output

If at least one enabled rule's pattern matches an added line — and, where the
rule declares a `files` list, `fnmatch` accepts `tool_input.file_path` against
at least one of its globs — then the script SHALL print to stdout a JSON
object of the form
`{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": <reason>}}`
and exit 0, where the reason names every violated rule's `name`, its
`message`, and one offending line per rule. When no rule matches, the script
SHALL exit 0 and print nothing.

#### Scenario: Deny names the rule and the redirect
- **WHEN** an added line matches the built-in `changelog-comment` rule
- **THEN** stdout carries a `permissionDecision` of `deny` and the reason
  contains `changelog-comment`, that rule's message, and the offending line

#### Scenario: A clean edit passes silently
- **WHEN** no added line matches any enabled rule
- **THEN** the script exits 0 with empty stdout

#### Scenario: File glob restricts a rule
- **GIVEN** a rule declaring `files: ["*.py"]`
- **WHEN** an added line in `notes.md` matches that rule's pattern
- **THEN** the call is not denied on that rule's account

### Requirement: Built-in default rules
id: guardrail-default-rules

The script SHALL ship exactly three built-in rules, active by default in every
repository, each matched per added line with Python `re.search`:
`changelog-comment` with pattern
`(?i)(?:#|//)\s*(?:added|updated|changed|fixed|new|refactored)\s*:` and a
message stating that change-log comments narrate the edit and must be dropped
or replaced by a constraint the code cannot show; `narrating-comment` with
pattern `(?i)(?:#|//)\s*(?:now|then|next|first|finally),?\s+(?:we|i|it)\s`
and a message stating that step-narration comments restate the next line and
must be deleted; and `filler-placeholder` with pattern
`(?i)(?:#|//)\s*(?:\.\.\.\s*)?(?:rest of |existing code|remains? unchanged|unchanged below|no changes? (?:here|needed))`
and a message stating that placeholder comments stand in for real content and
the full content must be written instead.

#### Scenario: A change-log comment is denied by default
- **GIVEN** no `.shipd-config.json` layer declaring `guardrails`
- **WHEN** an Edit adds the line `// Fixed: off-by-one in pager`
- **THEN** the call is denied citing `changelog-comment`

#### Scenario: A narration comment is denied by default
- **WHEN** an Edit adds the line `# now we build the index`
- **THEN** the call is denied citing `narrating-comment`

#### Scenario: A placeholder comment is denied by default
- **WHEN** a Write's content contains the line `// ... rest of the file`
- **THEN** the call is denied citing `filler-placeholder`

### Requirement: Fail-open behavior
id: guardrail-fail-open

If stdin is not parseable JSON, the resolved `guardrails` config value is
malformed, a rule's pattern does not compile, or any unexpected exception is
raised, then the script SHALL exit 0 without denying (malformed config is
treated as undeclared, so the built-in defaults still apply to the rest of the
evaluation where possible). Where the environment variable `SHIPD_GUARDRAILS`
equals `off`, the script SHALL exit 0 immediately with no output. The script
SHALL never exit non-zero.

#### Scenario: Garbage stdin passes through
- **WHEN** the script receives non-JSON stdin
- **THEN** it exits 0 and prints nothing

#### Scenario: The env bypass disables everything
- **GIVEN** `SHIPD_GUARDRAILS=off` in the environment
- **WHEN** a payload that would otherwise be denied is evaluated
- **THEN** the script exits 0 and prints nothing

#### Scenario: An uncompilable config rule is skipped
- **GIVEN** a config rule whose `pattern` is invalid regex
- **WHEN** a payload matching a built-in rule is evaluated
- **THEN** the invalid rule is skipped and the built-in rule still denies
