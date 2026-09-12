# skills-venn-diagram tasks

## 1. The diagram

- [x] 1.1 [req: cheatsheet-doc] In `docs/cheatsheet.md`, directly above the
      `## /s: commands` heading, add a `## How the skills overlap` heading
      followed by a blank line and one ```mermaid fence. The fence body is
      exactly these lines, in this order, with the indentation shown:

      ```
      venn-beta
        set loop["The core loop"]
          text "s:onboard  s:doctor  s:duck  s:plan  s:fix  s:review  s:drive  s:gate  s:status  s:document  s:worktree-hooks"
        set scale["Bigger than one change"]
          text "s:epic  s:prd  s:initiative  s:workspace  s:explain"
        set know["Knowledge"]
          text "s:remember  s:memory  s:forget"
        union loop,scale
          text "s:build  s:autopilot"
        union loop,know
          text "s:ask"
        union scale,know
          text "s:research  s:video-ingest"
        union loop,scale,know
          text "s:teach"
      ```

      Add no `title` line and no `style` line. Leave both tables untouched.

- [x] 1.2 [req: cheatsheet-doc] From the repository root run
      `python3 plugins/s/skills/document/scripts/docs_lint.py
      docs/cheatsheet.md` and confirm it exits 0, then run
      `wc -l docs/cheatsheet.md` and confirm the count is at most 250. Report
      any failure instead of marking this task done.

- [x] 1.3 [req: cheatsheet-doc] From the repository root run
      `python3 plugins/s/skills/build/scripts/render.py output
      docs/cheatsheet.md --plain` and confirm it exits 0 and prints the
      `venn-beta` fence source rather than raising — the terminal renderer
      does not draw this diagram type and must degrade to showing its source.

## 2. The README roster

- [x] 2.1 [req: readme-catalogs-the-plugin-s-skills] In `README.md`'s
      `## Skills` section, add a row for `/s:worktree-hooks` to the **The
      core loop** table, after the `/s:document` row. Write its description
      from the `description` frontmatter of
      `plugins/s/skills/worktree-hooks/SKILL.md`, in the one-to-two sentence
      style of the rows around it.

- [x] 2.2 [req: readme-catalogs-the-plugin-s-skills] In the same section, add
      rows for `/s:prd` and `/s:explain` to the **Bigger than one change**
      table — `/s:prd` after the `/s:epic` row, `/s:explain` after the
      `/s:initiative` row. Write each description from that skill's
      `description` frontmatter under `plugins/s/skills/<name>/SKILL.md`, in
      the style of the rows around it.

- [x] 2.3 [req: readme-catalogs-the-plugin-s-skills] From the repository root,
      list the directories under `plugins/s/skills/` and the `/s:` invocations
      in `README.md`'s three group tables, and confirm every directory appears
      in exactly one table and no table names a directory that does not exist.
      Report any mismatch instead of marking this task done.

## 3. Verification

- [x] 3.1 [req: *] Confirm the diagram and the README agree: every `s:<name>`
      token inside the `venn-beta` fence in `docs/cheatsheet.md` names a
      directory under `plugins/s/skills/`, each such directory appears exactly
      once across all seven regions, and each skill's diagram region includes
      the group whose README table lists it. Report any mismatch instead of
      marking this task done.

## 4. Fix — a cheatsheet example that no longer runs

- [x] 4.1 [req: cheatsheet-doc] In `docs/cheatsheet.md` line 87, the `lint`
      row's example is `shipd lint docs-entry-merge`, naming a change that has
      since been archived, so it exits 1 instead of 0. Replace that example
      with the bare `shipd lint`, leaving the row's invocation column and
      description untouched. Then confirm from the repository root that
      `plugins/s/bin/shipd lint` exits 0 and that
      `python3 plugins/s/skills/document/scripts/docs_lint.py
      docs/cheatsheet.md` still exits 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 76 | 28.8k |
| (no tool) | 0 | 3.4k |
| Edit | 5 | 2.5k |
| Read | 10 | 2.0k |
| Agent | 3 | 1.5k |
| **Total** | 94 | 38.2k |
