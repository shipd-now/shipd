# markdown-render
Status: verified

## Idea

Add a `shipd render` verb that displays markdown — mermaid fences rendered as
ASCII/Unicode diagrams — in a plain `output` mode and an interactive `screen`
TUI, sharing one substitution function with the delivery board's markdown
panes and the `/s:explain` skill's diagrams.

### Motivation

Mermaid blocks are first-class in the spec surfaces (`/s:explain` diagrams,
epic overviews, plan findings) but nothing in the engine can render one: the
board's `Markdown` widgets show raw fences and a terminal transcript shows
mermaid source. The user wants diagrams readable as text everywhere, through
one shared code path.

### Details

- Vendor the MIT-licensed, stdlib-only, single-file renderer
  `beautiful_mermaid.py` (github.com/Orbiter/beautiful-mermaid-py, a port of
  lukilabs/beautiful-mermaid) into the engine scripts.
- New engine script `render.py`: a shared fence-substitution function plus
  `output` (styled stdout via `rich`, `--plain` for verbatim text) and
  `screen` (textual viewer) verbs.
- `shipd render` dispatch in the binary, mirroring `board`'s mode-word grammar
  (bare → screen, `output` → output).
- Route the board's two markdown panes through the same substitution.
- `/s:explain` renders an earned mermaid diagram to ASCII through
  `shipd render output --plain -`, falling back to the raw fence.

Affected capabilities: `shipd-cli` (modified), `delivery-dashboard`
(modified), `shipd-explain` (modified), `markdown-render` (added). Impact:
`plugins/s/bin/shipd`, `plugins/s/skills/build/scripts/render.py` (new),
`plugins/s/skills/build/scripts/beautiful_mermaid.py` (vendored),
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/explain/SKILL.md`, `plugins/s/.claude-plugin/plugin.json`
(bump to 0.6.176), `.shipd/constitution.md`, `AGENTS.md`. No new pip
dependencies.

### Non-goals

- No new pip/third-party dependency: the renderer is vendored stdlib-only
  Python; `requirements.txt` is unchanged (the `mermaid-ascii` Go-binary
  wheel was considered and rejected).
- No HTML/SVG/web rendering and no diagram support in other skills' output —
  only the render verb, the board panes, and `/s:explain`.
- No prose prettification inside the substitution function itself — styling
  is the display modes' job, so the board widget and `rich` each style prose
  their own way over identical substituted markdown.

## Implementation

- **Vendored renderer, not a dependency.** `beautiful_mermaid.py` (~3.7k
  lines, imports only `dataclasses`/`typing`/`argparse`/`re`) lands beside the
  engine scripts with a provenance header (upstream URL, MIT, upstream commit
  date). Verified in-session: renders `graph`/`flowchart` TD/TB/LR,
  `sequenceDiagram`, `stateDiagram-v2` (also class/ER per upstream); the
  library API is `render_mermaid_ascii(text, use_ascii=False, padding_x=6,
  padding_y=4, box_border_padding=1)`; an unsupported type (e.g. `pie`)
  raises, exercised via `python3 beautiful_mermaid.py <file>` exit 0 on
  supported inputs. Rejected: the PyPI `mermaid-ascii` package — a
  platform-wheel Go binary that would add a second scoped dependency, doctor
  check, and degradation path for fewer diagram types.
- **One substitution function.** `render.py` exposes
  `substitute_mermaid_fences(text, use_ascii=False) -> str`: scan for
  ```` ```mermaid ```` fences (optional leading whitespace), render each body
  with `render_mermaid_ascii`, and replace the fence with a ```` ```text ````
  fence holding the diagram; any exception leaves that fence byte-identical.
  Module scope imports stdlib + `beautiful_mermaid` only — importable and
  testable without `textual`/`rich` installed. This is the single code path
  the output mode, the screen mode, and the board all consume.
- **Output mode is styled by default.** `render.py output [file|-]`
  substitutes, then renders the whole markdown through
  `rich.console.Console.print(rich.markdown.Markdown(...))` — headings,
  lists, and fences styled; color only on a TTY (rich's own detection).
  `--plain` skips rich and prints the substituted markdown verbatim; the same
  plain path is the fallback (with one stderr note) when rich cannot be
  provisioned. `--ascii` passes `use_ascii=True` for 7-bit diagrams. Verified
  in-session: rich 15.0.0 is a dependency of the pinned textual 8.2.8 and
  `Console(force_terminal=False)` produced clean styled text for headings,
  lists, and a code fence. Rejected: a stdlib mini-prettifier — duplicates
  what rich already does and would drift from the board's look.
- **Screen mode is a textual viewer.** `render.py screen [file|-]` calls
  `tui_bootstrap.ensure_textual` (the board's self-provisioning path — rich
  arrives with textual, so `output`'s styled path reuses the same bootstrap)
  and runs a minimal app: a `VerticalScroll(Markdown(substituted))` with
  `q`/escape to quit — the same widget the board's panes use.
- **Dispatch mirrors board.** `bin/shipd` gains `RENDER_MODES` beside
  `BOARD_MODES`: `None -> ("render.py", ["screen"])`, `"output" ->
  ("render.py", ["output"])`; bare word consumed only as first trailing
  argument; unknown words fall through to the screen delegate; `render` joins
  the usage banner. Oracle-settled: the interactive default is the verified
  `shipd board` convention (`verified/shipd-cli`, `cli-dispatch`).
- **Board reuse.** `dashboard.py` imports `render.substitute_mermaid_fences`
  (stdlib-safe) and wraps the two `Markdown(...)` construction sites — the
  artifact tabs and the epic-overview pane — so board panes and `shipd
  render` show identical diagram text.
- **Explain integration.** The skill pipes the earned fenced mermaid block
  through `shipd render output --plain -` and embeds the returned
  ```` ```text ```` diagram; a non-zero exit or unchanged output falls back
  to emitting the mermaid fence as today. The skill's diagram guidance also
  notes the renderer's parsing quirk: edges need spaced arrows (`A --> B`);
  `A-->B` silently renders as a label box (observed in-session, exit 0).
- **Constitution and docs.** `.shipd/constitution.md`'s technology exception
  widens from "dashboard.py's tui rendering" to the display surfaces
  (dashboard tui and render.py's screen/output styling, textual plus its
  bundled rich); AGENTS.md's dependency section notes the vendored renderer.
  Engine test suite `tests/` still passes without textual/rich installed.

Risk: upstream renderer bugs (border-junction glyphs, the tight-arrow quirk)
become ours to carry; guarded by the leave-fence-unchanged fallback and by
pinning the vendored copy to a reviewed snapshot rather than tracking
upstream.

## Questions and answers

### Q1: What does output mode do with non-diagram prose?
- **Question:** Should `render output` pass markdown through verbatim with
  only mermaid fences replaced, or also prettify the prose? Options: (a)
  verbatim pass-through; (b) prettify. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Prettify — make output mode look as good as possible, reusing
  how the board already renders markdown, and keep the two on one shared
  function. Resolved as rich-styled output by default with `--plain` for the
  verbatim form.
- **Queued:** none — no workspace is discoverable from this repo, so nothing
  was filed.

### Q2: What does bare `shipd render <file>` default to?
- **Question:** Screen (TUI, matching `shipd board`), output (pipe-safe), or
  TTY auto-detection? Recommendation: screen.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Default to the interactive screen mode with `output` as the
  explicit consumed mode word — the verified convention of the binary's
  existing dual-mode verb, where bare `board` opens the TUI and the mode word
  `text` selects plain rendering; explicit mode words were deliberately
  chosen over TTY auto-detection.
- **Cited:** verified/shipd-cli
