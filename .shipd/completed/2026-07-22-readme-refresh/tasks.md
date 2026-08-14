## 1. Rewrite

- [x] 1.1 Rewrite `README.md` per design.md D1/D2: keep the banner and intro;
      replace the Skills table with three rows (`/s:plan`, `/s:build`,
      `/s:status`) paraphrasing each skill's `description` frontmatter from
      `plugins/s/skills/<name>/SKILL.md`; add "The spec engine",
      "Statusline", and "Build telemetry" sections with the content D1
      specifies (lifecycle line with stage meanings, guarded transitions +
      `--force`, statusline format + `use` + settings registration, config
      keys + builds.jsonl, link to `am/spec/README.md` for the grammar);
      update the Structure tree to the real layout (am/spec, three skills,
      integrations/statusline.sh, build scripts); keep Install,
      Adding a command, Adding a skill, and After editing sections intact.

## 2. Verify accuracy

- [x] 2.1 Check every claim per design.md D3 and fix discrepancies: skills
      table vs `ls plugins/s/skills/`; every path in the Structure tree
      exists on disk; statusline line format matches
      `plugins/s/integrations/statusline.sh`; config keys match
      `plugins/s/skills/build/references/shipd.config.example.json`;
      `grep -i openspec README.md` returns nothing.
