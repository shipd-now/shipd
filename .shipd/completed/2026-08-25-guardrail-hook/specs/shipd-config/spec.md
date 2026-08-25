## ADDED Requirements

### Requirement: Guardrails config key
id: guardrails-key

The configuration MAY declare `guardrails`, resolved through the standard
layered per-key merge (nearest layer wins the key wholesale): either the
boolean `false`, in which case the guardrail hook SHALL evaluate nothing and
allow every call; or an object with two optional members — `disable`, a list
of rule names to drop from the resolved registry, and `rules`, a list of rule
objects each carrying a required `name`, `pattern` (Python `re` syntax,
applied per added line with `re.search`), and `message`, plus an optional
`files` list of `fnmatch` globs tested against the tool call's `file_path`.
The hook SHALL build its registry by starting from the built-in rules in
order, replacing any built-in whose `name` a config rule repeats, appending
the remaining config rules, and then dropping every name listed in `disable`.
When no layer declares the key, the built-in rules SHALL all be active. If
the declared value is neither `false` nor such an object, then the hook SHALL
treat the key as undeclared rather than erroring.

#### Scenario: False disables the hook wholly
- **GIVEN** a layer declaring `"guardrails": false`
- **WHEN** an Edit adds a line matching a built-in rule
- **THEN** the hook allows the call

#### Scenario: Disable drops one built-in
- **GIVEN** a layer declaring `"guardrails": {"disable": ["narrating-comment"]}`
- **WHEN** an Edit adds a line matching only `narrating-comment`
- **THEN** the hook allows the call, while the other built-ins stay active

#### Scenario: A config rule extends the registry
- **GIVEN** a layer whose `guardrails.rules` adds a rule named `no-console-log`
  with pattern `console\.log\(` and a message
- **WHEN** an Edit adds a line `console.log(user)`
- **THEN** the hook denies the call citing `no-console-log`

#### Scenario: A same-named config rule replaces the built-in
- **GIVEN** a layer whose `guardrails.rules` declares a rule named
  `changelog-comment` with a different pattern
- **WHEN** the registry is resolved
- **THEN** it contains one `changelog-comment` rule carrying the config
  layer's pattern

#### Scenario: A malformed value is treated as undeclared
- **GIVEN** a layer declaring `"guardrails": "loud"`
- **WHEN** an Edit adds a line matching a built-in rule
- **THEN** the hook behaves as if no layer declared the key and denies the
  call on the built-in rule

### Requirement: Guardrails key documentation
id: guardrails-key-docs

The content directory's `README.md` (the format authority) SHALL document the
`guardrails` key: the `false` form, the object form with `disable` and
`rules` (including the rule object's `name`/`pattern`/`message`/`files`
members), the three built-in rule names active when the key is undeclared,
that resolution follows the standard layered per-key merge, and the
`SHIPD_GUARDRAILS=off` environment bypass. The copyable config example JSON
shipped in the plugin's build references SHALL name the optional `guardrails`
key with a pointer to that documentation, without actively declaring a value —
copying the file unchanged declares nothing.

#### Scenario: The format authority answers the key's usage
- **WHEN** a reader consults the content directory's `README.md` on
  `guardrails`
- **THEN** it states both forms, the rule object members, the built-in rule
  names, the layered resolution, and the environment bypass

#### Scenario: Config example points at the key
- **WHEN** a reader opens the copyable config example JSON
- **THEN** it mentions the optional `guardrails` key and where it is
  documented, declaring no value
