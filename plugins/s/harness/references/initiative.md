# /s:initiative reference — the brief contract

Author into a staging file (a `mktemp` path is fine) and let
`spec_emit.py initiative` install it. Never construct the workspace path
yourself.

```
# <slug>
Status: open
Project: <project-slug>    (optional — only a slug declared in the registry)

<one or two sentences stating the initiative's goal>

## Requirements

- [ ] <outcome the initiative must achieve>
- [ ] <another outcome>
```

## Rules the linter enforces

- **Title and status.** `# <slug>` matches the brief's directory. A new brief
  is `Status: open`; `review`'s `initiative-sync` owns every later transition.
- **Metadata.** `Project:` is the only recognized key: kebab-case, naming a
  project slug **declared in the workspace registry**. Omit the line entirely
  for an unscoped initiative. Where the registry declares no projects at all, a
  `Project:` line is an error.
- **Requirements.** A `## Requirements` section with at least one `- [ ]`
  checkbox. Each is phrased as an outcome the initiative achieves, not a task,
  and every one is emitted unticked.

## Where the work lands

- `new` and `review` affect only the workspace, outside the repository, so the
  repo's worktree-and-PR workflow does not apply to them.
- `list` reads only.
- `set` writes the epic's `Initiative:` line in the repository through
  `epic-set-initiative`, so it ships as a PR from its own worktree — never a
  direct commit to the default branch. Exactly one `Initiative:` line survives
  per epic; the verb replaces any existing one and preserves everything else.
