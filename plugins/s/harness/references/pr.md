# /s:pr — reference

The fuller rules behind the pull request writer.

## The body

| Part | Rule |
| --- | --- |
| Line 1 | `## ☕ Pull Request` |
| Why paragraph | what a person sees today, then what this change fixes; plain words |
| What changed | a short list, one bullet per user-visible effect |
| Footer | a `<sub>☕ Posted by Shipd</sub>` paragraph, directly before the last line |
| Last line | `🤖 Generated with [Claude Code](https://claude.com/claude-code)` |

The body is staged with `<!-- doc-type: concept -->` as line 1 so that
`docs_lint.py` accepts it. Lint until it exits 0, then strip the marker line
before posting.

## The title

`pr_title.py title --summary <s> [--ticket <t>] [--branch <b>]` renders the
`pr.title` template from the layered config. The default template is
`{summary}`.

- `{summary}` is the change's one-sentence summary, trimmed to about 60
  characters.
- `{ticket}` is the `--ticket` value, else the first match of
  `pr.ticket_pattern` in the branch name. With no ticket, it and the
  whitespace after it drop out.
- `{change}` is the slug of a `change/<slug>` branch, else empty.

An empty title or a bad `pr` config member exits 1 with an `Error:` line.

## What the caller owns

The caller pushes before `/s:pr`, arms auto-merge after it, and decides the
mode. `/s:pr` only creates or edits the pull request and prints its URL.
