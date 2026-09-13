# skills-venn-regions tasks

## 1. The diagram

- [x] 1.1 [req: cheatsheet-doc] In `docs/cheatsheet.md`, replace the body of
      the existing ```mermaid fence with exactly these lines, in this order,
      with the indentation shown. Leave the `## How the skills overlap`
      heading and the fence markers themselves as they are.

      ```
      venn-beta
        set loop["The core loop"]
          text "One change"
        set scale["Bigger than one change"]
          text "Many changes"
        set know["Knowledge"]
          text "Durable decisions"
        union loop,scale
          text "At scale"
        union loop,know
          text "Asks"
        union scale,know
          text "Evidence"
        union loop,scale,know
          text "Both"
      ```

- [x] 1.2 [req: cheatsheet-doc] In `docs/cheatsheet.md`, directly beneath the
      fence's closing marker, add a blank line and then this list verbatim:

      ```
      - **One change** — the core loop, one change from idea to merged:
        s:onboard, s:doctor, s:duck, s:plan, s:fix, s:review, s:drive,
        s:gate, s:status, s:document, s:worktree-hooks
      - **Many changes** — bigger than one change, tracked together: s:epic,
        s:prd, s:initiative, s:workspace, s:explain
      - **Durable decisions** — knowledge that outlives a change: s:remember,
        s:memory, s:forget
      - **At scale** — s:build, s:autopilot
      - **Asks** — s:ask
      - **Evidence** — s:research, s:video-ingest
      - **Both** — s:teach
      ```

## 2. Verification

- [x] 2.1 [req: cheatsheet-doc] From the repository root run
      `python3 plugins/s/skills/document/scripts/docs_lint.py
      docs/cheatsheet.md` and confirm it exits 0, then `wc -l
      docs/cheatsheet.md` and confirm the count is at most 250. Report any
      failure instead of marking this task done.

- [x] 2.2 [req: cheatsheet-doc] Confirm the fence names no skill: read the
      fence and check that none of its seven `text` lines contains the string
      `s:`, and that each `set` and `union` line is followed by exactly one
      indented `text` line.

- [x] 2.3 [req: *] Confirm the list is complete and exact: collect the
      `s:<name>` tokens from the list beneath the fence and compare them
      against the directory names under `plugins/s/skills/`. Every directory
      must appear exactly once, and no token may name a directory that does
      not exist. Then confirm each of the seven region names used in the fence
      appears as a bolded name in the list. Report any mismatch instead of
      marking this task done.

- [x] 2.4 [req: *] From the repository root run
      `python3 plugins/s/skills/build/scripts/render.py output
      docs/cheatsheet.md --plain` and confirm it exits 0 — the terminal
      renderer does not draw this diagram type and must degrade to printing
      the fence source rather than raising.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 675 | 357.2k |
| Edit | 40 | 45.2k |
| Write | 21 | 42.7k |
| (no tool) | 0 | 33.5k |
| Read | 70 | 15.8k |
| Agent | 15 | 9.3k |
| SendUserFile | 5 | 3.1k |
| ListAgents | 2 | 707 |
| ToolSearch | 1 | 512 |
| SendMessage | 1 | 462 |
| WebFetch | 1 | 363 |
| WebSearch | 2 | 158 |
| **Total** | 833 | 509.0k |
