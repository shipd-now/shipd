## MODIFIED Requirements

### Requirement: Diagrams only where they carry structure
id: explain-diagram-policy
base: d7906c0ea722

Where the epic's structure — member dependency order, a pipeline, or hand-offs
between actors — is conveyed faster by a picture than by prose, the skill SHALL
include a diagram as either swimlane-style ASCII or a mermaid block; otherwise
it SHALL include no diagram. When the skill authors a mermaid diagram, it
SHALL write edges with spaced arrows (`A --> B`, never `A-->B`), SHALL render
the fenced block to ASCII by piping it through
`shipd render output --plain -` and embed the returned ```` ```text ````
diagram block in the explanation instead of the mermaid source, and SHALL
fall back to emitting the mermaid fence unchanged if that render exits
non-zero or returns the fence unsubstituted.

#### Scenario: A multi-member dependency chain earns a diagram
- **WHEN** the epic's design orders several members along dependency or
  pipeline seams
- **THEN** the explanation includes one swimlane-style ASCII or mermaid
  diagram of that structure

#### Scenario: A simple epic gets prose only
- **WHEN** the epic's structure is a flat list with no ordering or hand-offs
  worth picturing
- **THEN** the explanation contains no diagram

#### Scenario: A mermaid diagram is delivered rendered
- **WHEN** the skill authors a supported mermaid diagram for an epic
- **THEN** the explanation embeds the ASCII rendering produced by
  `shipd render output --plain -` as a ```` ```text ```` block, not the raw
  mermaid source

#### Scenario: Render failure falls back to the mermaid fence
- **WHEN** the render invocation fails or leaves the fence unsubstituted
- **THEN** the explanation includes the original mermaid fence, and the skill
  still writes no file
