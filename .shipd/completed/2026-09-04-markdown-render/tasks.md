## 1. Vendored renderer

- [x] 1.1 [req: render-fence-substitution] Vendor the renderer: download
      https://raw.githubusercontent.com/Orbiter/beautiful-mermaid-py/main/beautiful_mermaid.py
      (MIT, ~3.7k lines, stdlib-only imports) to
      `plugins/s/skills/build/scripts/beautiful_mermaid.py`, and add a
      provenance comment block at the top (upstream repo URL, MIT license,
      retrieval date, note that the file is vendored verbatim below the
      block). Verify by piping `graph LR` with spaced arrows through
      `python3 beautiful_mermaid.py <tmpfile>` and observing box-drawing
      output with exit `0`.

## 2. Shared substitution core

- [x] 2.1 [req: render-fence-substitution] Add
      `plugins/s/skills/build/tests/test_render.py` covering
      `substitute_mermaid_fences`: a supported `graph LR` fence (spaced
      arrows) becomes a ```` ```text ```` fence containing box-drawing
      characters with surrounding prose byte-identical; an unsupported `pie`
      fence is left byte-identical; a non-mermaid ```` ```python ```` fence
      is untouched; `use_ascii=True` yields only 7-bit characters; and
      `import render` succeeds with `textual`/`rich` absent (the suite never
      installs them). Run it and observe it fail — `render.py` does not exist
      yet.
- [x] 2.2 [req: render-fence-substitution] Create
      `plugins/s/skills/build/scripts/render.py` with
      `substitute_mermaid_fences(text, use_ascii=False)`: line-scan for
      ```` ```mermaid ```` fences (optional leading whitespace, closing
      ```` ``` ```` at matching or lesser indent), render each body via
      `beautiful_mermaid.render_mermaid_ascii(body, use_ascii=use_ascii)`
      inside `try/except Exception`, replace the fence with a
      ```` ```text ```` fence holding the rendering on success and leave it
      unchanged on failure. Module scope imports stdlib +
      `beautiful_mermaid` only. Confirm the 2.1 tests pass.

## 3. Output mode

- [x] 3.1 [req: render-output-mode] Extend `tests/test_render.py` with
      subprocess tests of `render.py output`: `--plain -` on stdin markdown
      with a supported fence prints the substituted markdown and exits `0`;
      `--plain --ascii -` yields 7-bit diagram characters; a missing file
      argument prints an `Error:` line to stderr and exits non-zero. Run and
      observe the new tests fail.
- [x] 3.2 [req: render-output-mode] Implement the `output` verb in
      `render.py` (argparse subcommand, `cli_common` error conventions):
      read the file or stdin (`-`), substitute, then — unless `--plain` —
      provision rich via `tui_bootstrap.ensure_textual` and print through
      `rich.console.Console().print(rich.markdown.Markdown(text))`; on a
      provisioning failure print one note to stderr and fall back to the
      plain rendering with exit `0`. `--plain` never imports rich. Confirm
      the 3.1 tests pass.

## 4. Screen mode

- [x] 4.1 [req: render-screen-mode] Add
      `plugins/s/skills/build/tests_textual/test_render_screen.py` using
      textual's pilot: the viewer app for markdown holding a supported
      mermaid fence mounts a `Markdown` widget whose document is the
      substituted text (assert the ```` ```text ```` diagram content), and
      pressing `q` exits the app. Run and observe it fail.
- [x] 4.2 [req: render-screen-mode] Implement the `screen` verb in
      `render.py`: call `tui_bootstrap.ensure_textual` from the script entry
      (mirroring `dashboard.py`), then run a minimal textual App composing
      `VerticalScroll(Markdown(substituted))` with bindings `q`/`escape` →
      exit. Confirm the 4.1 tests pass under `tests_textual`.

## 5. Binary dispatch

- [x] 5.1 [req: cli-dispatch] Extend the binary's dispatch tests (the
      `tests/` module covering `bin/shipd`'s verb table and `BOARD_MODES`)
      with render-mode cases: `shipd render --help` matches
      `render.py screen --help` output and exit `0`; `shipd render output
      --plain <file>` matches `render.py output --plain <file>`; an unknown
      first mode word falls through to the screen delegate; `shipd --help`
      lists `render`. Run and observe them fail.
- [x] 5.2 [req: cli-dispatch] In `plugins/s/bin/shipd`, add `RENDER_MODES =
      {None: ("render.py", ["screen"]), "output": ("render.py", ["output"])}`
      beside `BOARD_MODES`, dispatch `render` through it exactly as `board`
      dispatches (first-trailing-bare-word rule), and add the `render` line
      to `USAGE`. Confirm the 5.1 tests pass.

## 6. Board integration

- [x] 6.1 [req: board-markdown-diagrams] Extend
      `tests_textual/` board modal tests: an artifact text and an epic
      overview holding a supported mermaid fence reach their `Markdown`
      widgets with the fence replaced by a ```` ```text ```` diagram block,
      and an unparseable fence arrives unchanged. Run and observe them fail.
- [x] 6.2 [req: board-markdown-diagrams] In
      `plugins/s/skills/build/scripts/dashboard.py`, import
      `render.substitute_mermaid_fences` at module scope (stdlib-safe) and
      apply it to the markdown text at both construction sites — the
      artifact tabs (`_artifact_tabs`, the `Markdown(artifact["text"])`
      call) and the epic overview (`Markdown(text)` in the epic modal).
      Confirm the 6.1 tests pass and `tests/` still passes without textual
      installed.

## 7. Explain skill, docs, version

- [x] 7.1 [req: explain-diagram-policy] In
      `plugins/s/skills/explain/SKILL.md` section 3, require spaced arrows
      (`A --> B`, never `A-->B` — the renderer silently draws a label box
      otherwise) and instruct: render an earned mermaid diagram by piping
      the fenced block through `shipd render output --plain -`, embed the
      returned ```` ```text ```` block instead of the mermaid source, and
      fall back to the raw mermaid fence when the command exits non-zero or
      returns the fence unsubstituted; note this pipe writes no file, so the
      read-only contract holds.
- [x] 7.2 [req: *] Update `.shipd/constitution.md`'s technology-constraint
      exception to cover the display surfaces (dashboard.py's `tui` and
      render.py's `screen`/styled `output`, which may import the pinned
      `textual` and the `rich` it bundles) and note the vendored
      `beautiful_mermaid.py` stays stdlib-only; update `AGENTS.md`'s
      third-party-dependency section with the same two facts; bump
      `plugins/s/.claude-plugin/plugin.json` to `0.6.176`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 139 | 34.5k |
| Edit | 24 | 5.7k |
| Write | 3 | 2.7k |
| Read | 29 | 1.6k |
| Agent | 2 | 1.3k |
| (no tool) | 0 | 303 |
| ToolSearch | 2 | 48 |
| **Total** | 199 | 46.3k |
