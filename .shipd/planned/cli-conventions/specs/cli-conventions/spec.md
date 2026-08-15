## ADDED Requirements

### Requirement: Error output convention
id: error-output-convention

Every engine CLI under `plugins/s/skills/build/scripts/` and the `shipd`
binary SHALL report a fatal error as a single `Error: <reason>` line on
stderr and exit nonzero, and SHALL report a usage error (unknown or missing
verb, invalid arguments) with usage text on stderr and exit 2. A shared
stdlib helper (`cli_common.err` / `cli_common.warn`) SHALL be the single
implementation of the error and warning line format, and callers SHALL keep
owning their exit codes.

#### Scenario: Fatal errors are one Error line on stderr
- **WHEN** `spec_status.py locate no-such-change` runs in a repo without that
  change
- **THEN** stderr carries a single line beginning `Error: ` and the exit code
  is nonzero

#### Scenario: Usage errors exit 2
- **WHEN** `shipd frobnicate` runs
- **THEN** the usage banner is printed to stderr and the exit code is 2

### Requirement: TTY-gated color
id: tty-gated-color

Where an error or warning line's target stream is a terminal (TTY) and the
`NO_COLOR` environment variable is unset or empty, the shared helper SHALL
color the `Error:` prefix red and the `WARNING:` prefix yellow using ANSI
escape sequences. If the stream is not a TTY, or `NO_COLOR` is set to any
non-empty value, then the helper SHALL emit plain text with no escape
sequences — byte-identical to the pre-color output — so piped and redirected
output, and every scenario that pins exact stderr text, is unaffected.

#### Scenario: Piped output carries no escape sequences
- **WHEN** an engine CLI error is captured through a pipe
- **THEN** the stderr bytes contain no ANSI escape sequences and read exactly
  `Error: <reason>`

#### Scenario: A terminal gets a colored prefix
- **WHEN** an error line is written to a pseudo-terminal with `NO_COLOR`
  unset
- **THEN** the `Error:` prefix is wrapped in ANSI color sequences and the
  reason text is unchanged

#### Scenario: NO_COLOR suppresses color on a terminal
- **WHEN** an error line is written to a pseudo-terminal with `NO_COLOR=1`
- **THEN** the output carries no ANSI escape sequences
