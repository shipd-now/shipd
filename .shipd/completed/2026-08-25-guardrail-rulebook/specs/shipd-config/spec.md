## MODIFIED Requirements

### Requirement: Guardrails config key
id: guardrails-key
base: 57f24b522386

The configuration MAY declare `guardrails`, resolved through the standard
layered per-key merge (nearest layer wins the key wholesale): either the
boolean `false`, in which case the guardrail hook SHALL evaluate nothing and
allow every call; or an object whose single recognized member is the optional
`disable`, a list of rule names dropped from the resolved registry after the
rulebook sources merge. Rule definitions themselves live in the markdown
rulebook (guardrail-rulebook-format), not in configuration: if the object
carries a `rules` member — the surface this key held before the rulebook —
then the hook SHALL ignore that member without erroring, and other
unrecognized members SHALL likewise be ignored. When no layer declares the
key, every rulebook source SHALL be active. If the declared value is neither
`false` nor an object, then the hook SHALL treat the key as undeclared rather
than erroring.

#### Scenario: False disables the hook wholly
- **GIVEN** a layer declaring `"guardrails": false`
- **WHEN** an Edit adds a line matching a built-in rule
- **THEN** the hook allows the call

#### Scenario: Disable drops one built-in
- **GIVEN** a layer declaring `"guardrails": {"disable": ["narrating-comment"]}`
- **WHEN** an Edit adds a line matching only `narrating-comment`
- **THEN** the hook allows the call, while the other built-ins stay active

#### Scenario: A legacy rules member is ignored
- **GIVEN** a layer whose `guardrails` object carries a `rules` list adding a
  rule named `no-console-log`
- **WHEN** an Edit adds `console.log(user)`
- **THEN** the hook does not deny on `no-console-log`, and the built-ins stay
  active

#### Scenario: A malformed value is treated as undeclared
- **GIVEN** a layer declaring `"guardrails": "loud"`
- **WHEN** an Edit adds a line matching a built-in rule
- **THEN** the hook behaves as if no layer declared the key and denies the
  call on the built-in rule

### Requirement: Guardrails key documentation
id: guardrails-key-docs
base: 48728c309867

The content directory's `README.md` (the format authority) SHALL document the
guardrail rulebook and its config key: the rule file format (frontmatter
`pattern`/`mode`/`files`/`cooldown`, the message body, `deny` as the default
mode and `remind` as the non-blocking mode), the three rule sources and their
precedence (repo `<content-dir>/rules/`, then `~/.shipd/rules/`, then the
plugin built-ins), the remind cooldown behavior (once per session by default,
`cooldown` seconds to re-arm), the config key's two forms (`false`, and the
object with `disable` — noting that the former `rules` member is superseded by
the rulebook and now ignored), and the `SHIPD_GUARDRAILS=off` environment
bypass. The copyable config example JSON shipped in the plugin's build
references SHALL name the optional `guardrails` key and the rulebook
directories with a pointer to that documentation, without actively declaring
a value — copying the file unchanged declares nothing. The repository SHALL
also ship a standalone guide at `docs/guardrails.md` covering: how the hook
works (PreToolUse deny and PostToolUse remind, evaluated over added lines
only), the rule file format with a worked example, the three rule sources and
their precedence, adding, editing, and overriding rules (including a
same-named override of a built-in), the config kill-switches and the
environment bypass, remind cooldown behavior, and the token-cost properties —
that rules consume no model context until one fires, that a firing deny costs
the retried edit while a firing remind costs one injected reminder, and the
deny-for-certain / remind-for-fuzzy authoring guidance.

#### Scenario: The format authority answers the rulebook's usage
- **WHEN** a reader consults the content directory's `README.md` on
  `guardrails`
- **THEN** it states the rule file format and both modes, the three sources
  and their precedence, the cooldown behavior, both config forms with the
  superseded `rules` member noted, and the environment bypass

#### Scenario: Config example points at the key and the rulebook
- **WHEN** a reader opens the copyable config example JSON
- **THEN** it mentions the optional `guardrails` key and the rulebook
  directories and where they are documented, declaring no value

#### Scenario: The standalone guide explains the system and its token cost
- **WHEN** a reader opens `docs/guardrails.md`
- **THEN** it explains both hook events over added lines, the rule format
  with a worked example, the sources and their precedence, and states that
  rules consume no model context until one fires
