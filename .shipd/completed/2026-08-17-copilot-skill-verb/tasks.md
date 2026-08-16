## 1. Integration templates

- [x] 1.1 [req: skill-template, setup-workflow-template] Create
      `plugins/s/skills/build/tests/test_copilot_verb.py` (subprocess-against-
      temp-roots style of `test_shipd_cli.py`) with template-content tests:
      `plugins/s/integrations/copilot/SKILL.md` exists with frontmatter
      `name`/`description`, the literal `<!-- shipd-copilot v{version} -->`
      line, the `files`/`diff`/`context` semdiff subcommand names, the
      high/medium/low rubric, and the no-model-pin documentation; and
      `plugins/s/integrations/copilot/copilot-code-review.yml` exists with the
      `# shipd-copilot v{version}` line, a single `copilot-setup-steps` job on
      `ubuntu-latest`, a difft-release install step, and a ripgrep install
      step. Run the file and observe it fail — the templates do not exist yet.
- [x] 1.2 [req: skill-template] Write `plugins/s/integrations/copilot/SKILL.md`
      per the delta: frontmatter, marker line, bundled-engine instructions
      (semdiff `files`/`diff`/`context`, structural JSON over raw dumps),
      severity rubric and blocking rule, read-only and text-engine degradation
      statements, no-model-pin and advisory documentation.
- [x] 1.3 [req: setup-workflow-template] Write
      `plugins/s/integrations/copilot/copilot-code-review.yml` per the delta:
      marker line, one `copilot-setup-steps` job on `ubuntu-latest`, a step
      downloading the prebuilt `difft-x86_64-unknown-linux-gnu.tar.gz` from
      difftastic's GitHub releases and placing `difft` on `PATH` via
      `$GITHUB_PATH`, and an `apt-get install -y ripgrep` step; no secrets.
      Confirm the template tests from 1.1 now pass.

## 2. The copilot verb

- [x] 2.1 [req: copilot-verb] Extend `test_copilot_verb.py` with black-box
      verb tests driving `plugins/s/bin/shipd` by path against temp roots:
      bare report prints `absent` per managed file, exits `0`, creates
      nothing; `add` installs the three files with markers substituted to the
      plugin manifest version and `semdiff.py` byte-identical to
      `plugins/s/skills/review/scripts/semdiff.py`; repeated `add` after
      editing the installed marker to an older version rewrites at the current
      version; `add` with a marker-less existing workflow exits `1` naming it
      and writes nothing, then succeeds with `--force`; `remove` deletes the
      owned files and prunes the emptied `.github/skills/code-review` tree,
      exits `0` when already absent; `remove` with a marker-less SKILL.md
      exits `1` deleting nothing; bare report prints `stale` when the
      installed `semdiff.py` bytes differ. Run and observe the new tests fail.
- [x] 2.2 [req: copilot-verb] Implement `cmd_copilot` in `plugins/s/bin/shipd`:
      argparse over `action` (`add`/`remove`, optional), `--root` (default
      cwd), `--force`; template loading from `PLUGIN_ROOT / "integrations" /
      "copilot"`; `{version}` substitution from the manifest (the
      `cmd_version` read); ownership checks on the marker lines; atomic
      writes via the same-directory temp-file-and-rename pattern of
      `_write_settings`; the report/add/remove behaviors and exit codes
      exactly per the `copilot-verb` delta requirement. Confirm 2.1 passes.
- [x] 2.3 [req: cli-dispatch] Add `"copilot"` to the `VERBS` tuple in
      `plugins/s/skills/build/tests/test_shipd_cli.py` so the banner tests
      require it; run that file and observe the banner assertions fail.
- [x] 2.4 [req: cli-dispatch] In `plugins/s/bin/shipd`: route `copilot` to
      `cmd_copilot` in `main()`, add the verb line to `USAGE`
      (`copilot [add|remove]    maintain the Copilot code-review skill in a
      repo`), and update the module docstring's mutating-verb exception note
      to name both `statusline install` and `copilot add`/`remove`. Confirm
      `test_shipd_cli.py` passes.

## 3. Ship hygiene

- [x] 3.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.122` to `0.6.123` (every `plugins/s/` change bumps it).
- [x] 3.2 [req: *] Run the full stdlib suite
      `python3 -m unittest discover plugins/s/skills/build/tests/` without
      `textual`/`pydantic` installed and confirm it is green.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Edit | 15 | 24.0k |
| Bash | 59 | 21.6k |
| Write | 3 | 6.9k |
| (no tool) | 0 | 5.3k |
| Agent | 2 | 2.0k |
| Read | 13 | 1.9k |
| **Total** | 92 | 61.8k |
