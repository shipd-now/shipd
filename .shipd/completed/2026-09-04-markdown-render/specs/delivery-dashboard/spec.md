## ADDED Requirements

### Requirement: Board markdown panes render mermaid fences
id: board-markdown-diagrams

The board's markdown panes — the spec modal's artifact tabs and the epic
modal's overview — SHALL pass their markdown text through `render.py`'s
shared `substitute_mermaid_fences` before constructing the `Markdown` widget,
so a ```` ```mermaid ```` fence in an artifact or an epic file is shown as a
rendered ASCII diagram inside a code block instead of raw mermaid source. If
a fence cannot be rendered, then the pane SHALL show that fence unchanged, as
today.

#### Scenario: Artifact tab shows a rendered diagram
- **WHEN** a change's `plan.md` holding a supported ```` ```mermaid ````
  fence is opened in the spec modal's artifact tabs
- **THEN** the pane's Markdown widget receives the text with that fence
  replaced by a ```` ```text ```` block of box-drawing characters

#### Scenario: Epic overview shows a rendered diagram
- **WHEN** an epic's `epic.md` holding a supported mermaid fence is opened in
  the epic modal
- **THEN** the overview's Markdown widget receives the substituted text, and
  prose around the diagram is unchanged

#### Scenario: Unrenderable fence degrades to source
- **WHEN** an artifact holds a mermaid fence the renderer cannot parse
- **THEN** the pane shows the original mermaid fence as a code block, exactly
  as before this capability existed
