<!-- description: Write a shipd pull request's title and body, then create or update the pull request and print its URL. -->
# /s:pr — write a pull request's title and body

You write the title and the body of one shipd pull request, then create or
update it. Invoked as `/s:pr [--ticket <id>] [--draft] [--base <ref>]`. The
caller pushes the branch first and arms auto-merge afterwards; you do neither,
and you never read `pr-mode`.

<!-- include:preamble -->

1. **Read the change.** On a `change/<slug>` branch, read it with
   `python3 "$S/spec_status.py" cat change <slug>`; elsewhere read
   `git log <base>..HEAD`.
2. **Read the standard**, `skills/document/references/standard.md`, then draft
   the body: line 1 `## ☕ Shipd Pull Request`, a why-first paragraph, a short
   list of what changed, and the last line
   `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
3. **Lint it.** Stage it with a first-line `doc-type: concept` comment marker, run
   `python3 "$S/../../document/scripts/docs_lint.py" <file>` until it exits 0,
   then strip the marker line.
4. **Render the title** with `python3 "$S/../../pr/scripts/pr_title.py" title
   --summary "<summary>" --branch "$(git branch --show-current)"`, adding
   `--ticket <id>` when given.
5. **Create or update.** `gh pr create --title "<title>" --body-file <file>`,
   with `--draft` when asked; when the branch already has a pull request,
   `gh pr edit --title "<title>" --body-file <file>`.
6. **Report the pull request's full URL**, never just the number.

<!-- if:file-references -->
The body shape and the title rules are written out in {refs}/pr.md.
<!-- end -->
