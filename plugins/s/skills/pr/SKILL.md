---
name: pr
description: >-
  Write a shipd pull request's title and its `## ☕ Pull Request` body,
  then create the pull request with `gh pr create` (or update it with
  `gh pr edit` when the branch already has one) and print its full URL. The
  title follows the `pr` config template and can carry a ticket id; the body
  is held to the documentation standard and linted before it posts. Never
  pushes, arms auto-merge, or reads `pr-mode`: the caller does that. Use when
  asked to open a PR, write a PR description, or set a PR title. Trigger
  phrases: "open the PR", "write the PR description", "retitle the PR",
  "/s:pr".
---

# /s:pr — write a pull request's title and body

You write the title and the body of one shipd pull request, then create or
update it. The caller pushes the branch first and arms auto-merge afterwards;
you do neither.

You are invoked as `/s:pr [--ticket <id>] [--draft] [--base <ref>]`.
`--ticket` sets the ticket id for the title. `--draft` opens the pull request
as a draft. `--base` is the ref the pull request targets (default: the
repository's default branch).

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `shipd:pr
v<version>` in your first user-visible status sentence (e.g. "shipd:pr
v0.6.307 — writing the PR for change/add-x"), so the user can always see which
plugin snapshot the session is running.

## Harness plan mode

**Harness plan mode never replaces this skill's output.** When the session
is in Claude Code plan mode, run only this skill's read-only steps. Stop
before the first write and ask the user to exit plan mode and re-invoke.
Never write the harness plan file, call `ExitPlanMode`, or mix in plan
mode's outputs. Details:
`${CLAUDE_PLUGIN_ROOT}/skills/document/references/harness-plan-mode.md`.

## The flow

1. **Read the change.** On a `change/<slug>` branch, read the change with
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat change <slug>`:
   its `## Idea` gives the why, its tasks give what changed. On any other
   branch, read `git log <base>..HEAD` and the diff stat instead.
2. **Read the standard.** Read
   `${CLAUDE_PLUGIN_ROOT}/skills/document/references/standard.md` before you
   write a word of the body.
3. **Draft the body** in this order:
   - Line 1 is exactly `## ☕ Pull Request`.
   - A why-first paragraph: what a person sees today, and what this change
     fixes. Plain words, no file paths in this paragraph.
   - A short list of what changed, one bullet per user-visible effect.
   - A `<sub>☕ Posted by Shipd</sub>` paragraph, directly before the last
     line.
   - The last line is `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
4. **Lint it.** Save the body to a scratch file with `<!-- doc-type: concept -->`
   as line 1, above the heading. Run
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/docs_lint.py" <file>`
   and fix the body until it exits 0. Then strip the marker line, so the
   posted body starts with `## ☕ Pull Request`.
5. **Render the title.** Take the change's one-sentence summary, trimmed to
   about 60 characters, and run
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/pr/scripts/pr_title.py" title --summary "<summary>" --branch "$(git branch --show-current)"`,
   adding `--ticket <id>` when `/s:pr` got one. It applies the `pr.title`
   template and finds the ticket in the branch name through
   `pr.ticket_pattern`. When it exits non-zero, relay its `Error:` line and
   stop.
6. **Create or update.** When the branch has no pull request, run
   `gh pr create --title "<title>" --body-file <file>`, adding `--draft` when
   `/s:pr` got `--draft` and `--base <ref>` when it got `--base`. When
   `gh pr view` shows the branch already has one, run
   `gh pr edit --title "<title>" --body-file <file>` instead and leave the
   draft state as it is.
7. **Print the URL.** Run `gh pr view --json url -q .url` and report the full
   URL, never just the number.

## Boundaries

- You never push, never arm auto-merge, and never read `pr-mode`. The caller
  pushes before `/s:pr` and arms auto-merge after it, as its own mode says.
- You rewrite only the description of the one pull request you were run on.
- When `gh` or the lint fails in a way you cannot fix by editing the body,
  relay the error line as it stands and stop.

## Report

Close with the pull request's full URL, the title you used, and whether you
created or updated it.
