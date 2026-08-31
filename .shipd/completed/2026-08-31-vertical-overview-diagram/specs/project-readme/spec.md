## ADDED Requirements

### Requirement: What-is overview layout
id: what-is-overview-layout

`docs/what-is-shipd.md` SHALL present its "How it fits together" overview as a
vertically-oriented mermaid flowchart (`flowchart TD`), so the published docs
site renders it within the content column without horizontal scrolling, and
SHALL place the present-and-future paragraph (the one beginning "Today shipd
builds itself") after that diagram, as the document's closing prose.

#### Scenario: Overview diagram is vertical
- **WHEN** the mermaid fence in `docs/what-is-shipd.md` is inspected
- **THEN** its first line declares `flowchart TD`, and `flowchart LR` appears
  nowhere in the file

#### Scenario: Future paragraph closes the document
- **WHEN** `docs/what-is-shipd.md` is read top to bottom
- **THEN** the paragraph beginning "Today shipd builds itself" appears after
  the "How it fits together" mermaid fence, and no body prose follows it
