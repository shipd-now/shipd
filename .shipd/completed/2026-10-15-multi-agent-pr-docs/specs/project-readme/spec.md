## ADDED Requirements

### Requirement: Multi-agent PR entry links
id: multi-agent-pr-entry-links

The three entry surfaces SHALL link the Multi-agent PR concept doc.
`README.md`'s "Getting started" section SHALL carry one sentence that links
`docs/multi-agent-pr.md`. `docs/what-is-shipd.md` SHALL link
`multi-agent-pr.md` in a prose paragraph placed after its Mermaid diagram
and before the paragraph that opens "Today shipd builds itself", and SHALL
stay at 100 lines or fewer. The `/s:room` row of `docs/cheatsheet.md`'s
command table SHALL link `multi-agent-pr.md` in its description cell.

#### Scenario: README links the concept doc
- **WHEN** a reader opens the "Getting started" section of `README.md`
- **THEN** it contains a link to `docs/multi-agent-pr.md`

#### Scenario: Overview links the concept doc within its cap
- **WHEN** `docs_lint.py docs/what-is-shipd.md` runs and `wc -l` counts
  the file
- **THEN** the lint exits `0`, the count is 100 or fewer, and the text
  between the closing Mermaid fence and "Today shipd builds itself"
  contains a link to `multi-agent-pr.md`

#### Scenario: Cheatsheet row links the concept doc
- **WHEN** `docs_lint.py docs/cheatsheet.md` runs and the `/s:room` row of
  its command table is read
- **THEN** the lint exits `0` and the row contains a link to
  `multi-agent-pr.md`
