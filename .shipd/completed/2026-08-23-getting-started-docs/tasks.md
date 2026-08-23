## 1. The cheatsheet

- [x] 1.1 [req: cheatsheet-doc] Create `docs/cheatsheet.md` with a
      one-paragraph intro saying it is a lookup reference (pointing at
      `getting-started.md` for the walkthrough), a `## Conventions` section
      stating once the flags shared across verbs — `--json`, `--root DIR`,
      `--all` — and then a `## /s: commands` three-column markdown table
      (`Command`, `What it does`, `Example`) with one row per directory under
      `plugins/s/skills/`. Take each row's argument and option forms and its
      one-line description from that skill's
      `plugins/s/skills/<name>/SKILL.md` — the frontmatter `description` for
      the description, the body's invocation-form lines for the forms — and
      give each row exactly one short example.
- [x] 1.2 [req: cheatsheet-doc] Append a `## shipd CLI` section to
      `docs/cheatsheet.md` as a three-column table in the same shape, with one
      row per verb listed by `python3 plugins/s/bin/shipd --help`. Take each
      row's positional arguments and options from
      `python3 plugins/s/bin/shipd <verb> --help`, omit the flags already
      covered by `## Conventions`, and give each row exactly one short
      example that is read-only unless the verb only writes.

## 2. The guide

- [x] 2.1 [req: getting-started-doc] In `docs/getting-started.md`, add a link
      to `cheatsheet.md` in the closing `## Where you are now` section,
      alongside the existing links, described as the command lookup reference.

## 3. Verify

- [x] 3.1 [req: cheatsheet-doc] Compare the `/s:` table's rows against
      `ls plugins/s/skills` and the `shipd` table's rows against the verb
      block of `python3 plugins/s/bin/shipd --help`; confirm each set matches
      one-to-one with no missing and no extra row, and fix any mismatch.
- [x] 3.2 [req: cheatsheet-doc] Execute every read-only example in the
      `shipd` table verbatim from the repository root. Every example whose row
      names no precondition must exit zero — correct any that does not. For
      `workspace`, which exits 1 here because no ancestor `.shipd-config.json`
      declares a `workspace` key, keep the ordinary invocation as the example
      and add a short precondition note to that row instead.
- [x] 3.3 [req: getting-started-doc] Execute the documented install-mode
      statusline command verbatim against a populated plugin cache and
      confirm it renders the newest snapshot's statusline output.
- [x] 3.4 [req: *] Re-read `docs/getting-started.md` and `docs/cheatsheet.md`
      end to end confirming every named command exists as documented in the
      repo and every relative link resolves; fix any drift found.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 112 | 57.2k |
| (no tool) | 0 | 5.0k |
| Write | 1 | 2.9k |
| Read | 10 | 1.9k |
| Agent | 2 | 1.3k |
| SendMessage | 1 | 795 |
| Edit | 1 | 370 |
| **Total** | 127 | 69.5k |
