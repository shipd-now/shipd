# skills-venn-reframe tasks

## 1. The README headings

- [x] 1.1 [req: readme-catalogs-the-plugin-s-skills] In `README.md`'s
      `## Skills` section, rename the three group heading lines, leaving every
      table row beneath them exactly where it is:
      `**The core loop** — take one change from idea to merged.` becomes
      `**Pipeline** — spec, build and ship one change, end to end.`;
      `**Bigger than one change** — decompose, deliver, and track work at scale.`
      becomes `**Orchestration** — decompose a feature and drive its changes at
      scale.`; and
      `**Knowledge** — so a decision made once is never asked twice.` becomes
      `**Memory** — so a decision made once is never asked twice.`

## 2. The diagram

- [x] 2.1 [req: cheatsheet-doc] In `docs/cheatsheet.md`, replace the body of
      the ```mermaid fence with exactly these lines, in this order, with the
      indentation shown. Leave the heading and the fence markers as they are.

      ```
      venn-beta
        set loop["Pipeline"]
          text "Spec, build, ship"
        set scale["Orchestration"]
          text "Epics, driven"
        set know["Memory"]
          text "Decisions that stick"
        union loop,scale
          text "Unattended"
        union loop,know
          text "Asks first"
        union scale,know
          text "Evidence"
        union loop,scale,know
          text "Compounds"
      ```

- [x] 2.2 [req: cheatsheet-doc] In `docs/cheatsheet.md`, replace the list
      beneath the fence with exactly this, keeping the same twenty-five skills
      in the same regions:

      ```
      - **Spec, build, ship** — the pipeline, one change end to end: s:onboard,
        s:doctor, s:duck, s:plan, s:fix, s:review, s:drive, s:gate, s:status,
        s:document, s:worktree-hooks
      - **Epics, driven** — orchestration across many changes: s:epic, s:prd,
        s:initiative, s:workspace, s:explain
      - **Decisions that stick** — memory that outlives a change: s:remember,
        s:memory, s:forget
      - **Unattended** — s:build, s:autopilot
      - **Asks first** — s:ask
      - **Evidence** — s:research, s:video-ingest
      - **Compounds** — s:teach
      ```

## 3. Verification

- [x] 3.1 [req: readme-catalogs-the-plugin-s-skills] Confirm the README still
      partitions the skill set: collect the `/s:` invocations under each of the
      three group tables and check that every directory under
      `plugins/s/skills/` appears in exactly one, with no extras. Confirm the
      three headings now read `**Pipeline**`, `**Orchestration**` and
      `**Memory**` in that order. Report any mismatch instead of marking this
      task done.

- [x] 3.2 [req: cheatsheet-doc] From the repository root run
      `python3 plugins/s/skills/document/scripts/docs_lint.py
      docs/cheatsheet.md` and confirm it exits 0, then `wc -l
      docs/cheatsheet.md` and confirm the count is at most 250.

- [x] 3.3 [req: *] Confirm the two surfaces agree: every `s:<name>` in the
      list beneath the fence names a directory under `plugins/s/skills/` and
      appears exactly once; none of the fence's seven `text` lines contains
      `s:`; each of the three pairwise regions and the centre carries at most
      two words; and each of the seven region names appears as a bolded name in
      the list. Report any mismatch instead of marking this task done.

- [x] 3.4 [req: *] From the repository root run
      `python3 plugins/s/skills/build/scripts/render.py output
      docs/cheatsheet.md --plain` and confirm it exits 0.
