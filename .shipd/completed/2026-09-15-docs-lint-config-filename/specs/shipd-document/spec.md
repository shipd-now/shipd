# shipd-document

## MODIFIED Requirements

### Requirement: Stdlib-only lint over the checkable rules
id: document-lint-cli
base: 2d365062b14f

`plugins/s/skills/document/scripts/docs_lint.py` SHALL be stdlib-only Python 3
and SHALL check, over prose outside code fences: sentence word caps (20 words
inside numbered-list items, 25 elsewhere), paragraphs over 6 sentences, the
doc-type marker and its line cap, and the mermaid-fence count — each as an
error. It SHALL additionally check, over every line of the file including
fenced blocks, that no page names a shipd configuration file the engine does
not read: the spellings `shipd.config.json` and a `shipd-config.json` that no
dot, word character, or hyphen precedes SHALL each be an error naming
`.shipd-config.json` as the file the engine reads. The sample filename
`shipd.config.example.json` SHALL NOT be an error. It SHALL report
passive-voice matches as warnings that never affect the exit code. If a
sentence boundary follows a known abbreviation (e.g., i.e., etc., vs.) or
falls inside an inline-code span, then the linter SHALL NOT split the sentence
there. Findings SHALL print as `file:line: error|warning: message`; the exit
code SHALL be 0 with no errors, 1 with any error, and 2 on usage or
unreadable-file problems.

#### Scenario: Long descriptive sentence is an error
- **WHEN** a doc paragraph contains a 30-word sentence outside any numbered
  list
- **THEN** the lint prints a `file:line: error:` finding naming the 25-word
  cap and exits 1

#### Scenario: Long procedural sentence uses the tighter cap
- **WHEN** a numbered-list item contains a 22-word sentence
- **THEN** the lint reports an error naming the 20-word procedural cap

#### Scenario: Passive voice is warning-only
- **WHEN** a doc's only finding is a passive-voice match
- **THEN** the lint prints a `warning:` line and exits 0

#### Scenario: Clean doc exits 0
- **WHEN** the lint runs on a conforming doc
- **THEN** it prints nothing (or only warnings) and exits 0

#### Scenario: A doc naming shipd.config.json is an error
- **WHEN** the lint runs on a doc whose prose names `shipd.config.json`
- **THEN** it prints a `file:line: error:` finding naming `.shipd-config.json`
  as the file the engine reads, and exits 1

#### Scenario: The correct filename is clean
- **WHEN** the lint runs on a conforming doc naming `.shipd-config.json`
- **THEN** it reports no error for that name and exits 0

#### Scenario: The sample filename is clean
- **WHEN** the lint runs on a conforming doc naming
  `shipd.config.example.json`
- **THEN** it reports no error for that name and exits 0

#### Scenario: A wrong filename inside a code fence is still an error
- **WHEN** the lint runs on a doc naming `shipd.config.json` only inside a
  fenced code block
- **THEN** it reports the error and exits 1

#### Scenario: The standard records the rule
- **WHEN** `plugins/s/skills/document/references/standard.md` is inspected
- **THEN** it states that a doc naming a configuration file other than
  `.shipd-config.json` is an error
