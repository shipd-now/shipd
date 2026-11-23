# factory-doc-always-on tasks

Apply both edits through `/s:document`. `artefacts/shipd-factory.md` is the binding text of the concept page; do not reword it.

## 1. Concept page

- [x] 1.1 [req: shipd-factory-page] Through `/s:document`, replace the whole content of `docs/shipd-factory.md` with the content of this change's `artefacts/shipd-factory.md`, unchanged.
- [x] 1.2 [req: shipd-factory-page] Run `diff docs/shipd-factory.md .shipd/planned/factory-doc-always-on/artefacts/shipd-factory.md` and confirm it prints nothing.

## 2. Setup page link

- [x] 2.1 [req: shipd-factory-page] In `docs/shipd-factory-setup.md` line 150, replace `[Set up a repo](shipd-factory.md#set-up-a-repo)` with `[Set up and remove](shipd-factory.md#set-up-and-remove)`. Change nothing else in the file.

## 3. Verify

- [x] 3.1 [req: shipd-factory-page] Run `python3 -B plugins/s/skills/document/scripts/docs_lint.py docs/shipd-factory.md docs/shipd-factory-setup.md` and confirm it exits 0.
- [x] 3.2 [req: shipd-factory-page] Run `wc -l docs/shipd-factory.md docs/shipd-factory-setup.md` and confirm it prints 100 and 150.
- [x] 3.3 [req: shipd-factory-page] Run `grep -c '(planned)' docs/shipd-factory.md` and confirm it prints 0. Run `grep -n -i -E 'a[x]el|100\.121\.|mikkel-bergmann/(shipd-factory|css-animation)' docs/shipd-factory.md` and confirm it prints nothing.
- [x] 3.4 [req: *] Run `python3 plugins/s/skills/build/scripts/spec_lint.py` and `python3 -B -m unittest discover -s plugins/s/skills/document/tests`, and confirm both exit 0.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 62 | 37.5k |
| SubagentHandback | 3 | 6.4k |
| Agent | 3 | 2.5k |
| (no tool) | 0 | 1.4k |
| Read | 7 | 1.0k |
| Edit | 2 | 842 |
| Skill | 4 | 551 |
| **Total** | 81 | 50.2k |
