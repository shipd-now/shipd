# markdown-render

### Requirement: Shared mermaid fence substitution
id: render-fence-substitution

The engine SHALL provide a stdlib-importable substitution function in
`render.py` — `substitute_mermaid_fences(text, use_ascii=False)` — that
replaces every ```` ```mermaid ```` fenced block in a markdown string with a
```` ```text ```` fenced block holding the diagram rendered by the vendored
`beautiful_mermaid.render_mermaid_ascii`, and leaves all other content
byte-identical. If rendering a fence raises any exception, then the function
SHALL leave that fence unchanged. The module SHALL import only the Python
standard library and the vendored `beautiful_mermaid` at module scope, so it
is importable without `textual` or `rich` installed.

#### Scenario: Supported fence becomes a rendered diagram
- **WHEN** `substitute_mermaid_fences` is called on markdown holding a
  ```` ```mermaid ```` fence with `graph LR` content using spaced arrows
- **THEN** the result holds a ```` ```text ```` fence containing box-drawing
  characters in place of the mermaid fence, and all surrounding prose is
  unchanged

#### Scenario: Unsupported fence is left untouched
- **WHEN** the markdown holds a ```` ```mermaid ```` fence with a `pie`
  diagram the renderer cannot parse
- **THEN** the returned text still holds that mermaid fence byte-identical

#### Scenario: ASCII-only charset
- **WHEN** `substitute_mermaid_fences` is called with `use_ascii=True`
- **THEN** the rendered diagram uses only 7-bit characters (`+`, `-`, `|`)
  instead of Unicode box drawing

#### Scenario: Importable without display dependencies
- **WHEN** `render.py` is imported in an environment without `textual` or
  `rich`
- **THEN** the import succeeds and the substitution function is usable

### Requirement: Styled output mode
id: render-output-mode

The engine SHALL provide a `render.py output [file]` verb that reads markdown
from the file argument (or stdin when the argument is `-`), applies the shared
substitution, and prints the result styled through `rich`'s markdown renderer
to stdout. Where `--plain` is given, the verb SHALL print the substituted
markdown verbatim without importing rich. Where `--ascii` is given, the verb
SHALL render diagrams with the 7-bit charset. If rich cannot be provisioned,
then the verb SHALL fall back to the plain rendering with a single note on
stderr and still exit `0`. If the file argument cannot be read, then the verb
SHALL print an `Error:` line to stderr and exit non-zero.

#### Scenario: Plain output from stdin
- **WHEN** markdown holding a supported mermaid fence is piped to
  `render.py output --plain -`
- **THEN** stdout holds the input markdown with the fence replaced by a
  ```` ```text ```` diagram block, nothing else is reformatted, and the exit
  code is `0`

#### Scenario: Styled output renders prose
- **WHEN** `render.py output <file>` runs with rich available
- **THEN** stdout holds rich-styled text (headings and lists formatted, no
  raw `#` heading markers) with the diagram preserved in a monospace block

#### Scenario: Missing file is an error
- **WHEN** `render.py output /no/such/file.md` runs
- **THEN** an `Error:` line is printed to stderr and the exit code is non-zero

### Requirement: Interactive screen mode
id: render-screen-mode

The engine SHALL provide a `render.py screen [file]` verb that self-provisions
`textual` through the board's `tui_bootstrap.ensure_textual` path and runs a
full-screen viewer holding the substituted markdown in a scrollable textual
`Markdown` widget — the same widget family the delivery board's panes use —
quitting on `q` or escape.

#### Scenario: Screen mode shows the substituted document
- **WHEN** `render.py screen <file>` runs on markdown holding a supported
  mermaid fence
- **THEN** the app's Markdown widget receives the substituted text, with the
  diagram in a ```` ```text ```` block

#### Scenario: Quit key ends the app
- **WHEN** `q` is pressed in the running viewer
- **THEN** the app exits with code `0`
