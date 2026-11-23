# Tasks — getting-started-five-steps

Rules for every task:

- Run every command from the repository root of this worktree.
- "Lint" means `python3 plugins/s/skills/document/scripts/docs_lint.py <file>`
  exits 0.
- `artefacts/` means `.shipd/planned/getting-started-five-steps/artefacts/`.
- Write no prose of your own. If an old text is not found exactly once, stop
  and report it; do not reword.

## 1. Docs pages

- [x] 1.1 [req: getting-started-doc, first-change-guide-owners, pipeline-follower-docs]
      Copy `artefacts/getting-started.md` over `docs/getting-started.md`,
      byte for byte. Run `cmp` on the two files and confirm no output. Lint
      `docs/getting-started.md` and confirm `wc -l` prints 99.
- [x] 1.2 [req: onboard-user-docs] Copy `artefacts/onboard.md` to the new
      file `docs/onboard.md`, byte for byte. Run `cmp` on the two files and
      confirm no output. Lint `docs/onboard.md` and confirm `wc -l` prints
      73.
- [x] 1.3 [req: cheatsheet-page-links] In `docs/cheatsheet.md`, replace the
      text `See [Your first change](getting-started.md). | ` followed by
      `` `/s:onboard next` `` with `See [Guided tour](onboard.md). | `
      followed by `` `/s:onboard next` ``. The old text sits once, in the
      `/s:onboard` row. Change nothing else in the file. Lint it.

## 2. Verify

- [x] 2.1 [req: first-change-guide-owners] Run
      `grep -n "^#" docs/getting-started.md` and confirm
      the headings are `# Your first change`, `## 1. Install`,
      `## 2. Plan your first change`, `## 3. Build it`,
      `## 4. Turn on the statusline`, `## 5. Watch the board`, and
      `## Where to go next`, in that order. Run
      `grep -n "getting-started.md#" docs/*.md` and confirm the only anchor
      is `#1-install`.
- [x] 2.2 [req: pipeline-follower-docs, first-change-guide-owners] Run
      `grep -n "onboard\|shipd doctor\|doctor.md\|autonomous-pipeline\|autoUpdate\|shipd update" docs/getting-started.md`
      and confirm no line matches. Run
      `grep -n "autonomous-pipeline" README.md` and confirm no line
      matches. Run `grep -c "eco" docs/customise.md` and confirm it prints
      1 or more.
- [x] 2.3 [req: getting-started-doc] Run
      `grep -n "<details>\|<summary>Alternative install</summary>\|</details>\|Claude Code only\|shipd statusline install\|shipd board" docs/getting-started.md`
      and confirm exactly six lines match.
- [x] 2.4 [req: cheatsheet-page-links] Run
      `grep -n "getting-started.md" docs/cheatsheet.md` and confirm one
      line matches, the intro line. Run `grep -c "(onboard.md)"
      docs/cheatsheet.md` and confirm it prints 1.
- [x] 2.5 [req: *] For `docs/getting-started.md` and `docs/onboard.md`, list
      every relative link target with
      `grep -o "]([^)#]*" <file> | grep -v "http" | cut -c3-` and confirm
      each names an existing file relative to `docs/`.
- [x] 2.6 [req: *] Run the CI docs lint: `python3
      plugins/s/skills/document/scripts/docs_lint.py $(find docs -name
      "*.md" -not -path "docs/retros/*")` and confirm exit 0.
- [x] 2.7 [req: *] Run `python3 -B -m unittest discover -s
      plugins/s/skills/build/tests` and
      `python3 -B -m unittest discover -s plugins/s/skills/document/tests`.
      For each, grep the output, stderr included, for the `OK` or `FAILED`
      verdict line and confirm `OK`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 34 | 13.0k |
| Write | 2 | 2.6k |
| Agent | 2 | 2.1k |
| SubagentHandback | 1 | 1.6k |
| ToolSearch | 2 | 975 |
| Monitor | 2 | 535 |
| (no tool) | 0 | 312 |
| Edit | 1 | 193 |
| Read | 1 | 147 |
| **Total** | 45 | 21.5k |
