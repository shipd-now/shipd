## MODIFIED Requirements

### Requirement: Guardrails key documentation
id: guardrails-key-docs
base: ba070919e767

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
deny-for-certain / remind-for-fuzzy authoring guidance. The standalone guide
SHALL conform to the shipd documentation standard:
`<!-- doc-type: reference -->` as its first line and a total line count
within the reference cap.

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

#### Scenario: The standalone guide carries its marker and fits its cap
- **WHEN** `docs_lint.py` runs over `docs/guardrails.md`
- **THEN** it exits 0 with the file marked `reference`
