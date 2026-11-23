## ADDED Requirements

### Requirement: Initiatives user documentation
id: initiatives-user-docs

The repository SHALL provide `docs/initiatives.md`, the main page for
`/s:initiative`, titled "Initiatives". The page SHALL conform to the shipd
documentation standard with `<!-- doc-type: how-to -->` as its first line,
and SHALL open by saying what an initiative is, then hold exactly three level-2
sections in this order: `## When to use it`, `## How to run it`, and
`## Reference`.

The page SHALL state:

- that an initiative is a workspace brief stating the outcomes an epic
  delivers against, and that it sits above epics;
- that a brief lives in the workspace, at `initiatives/<slug>/brief.md`
  under the workspace's content directory, and that every verb needs a
  discoverable workspace;
- the shape of a brief in one example fence: the title, `Status: open`, the
  optional `Project:` line, a goal sentence, and a `## Requirements` list of
  checkbox outcomes;
- that a requirement is an outcome, never a task;
- the three statuses `open`, `achieved`, and `dropped`, and that `achieved`
  is derived once every requirement is ticked;
- the run as numbered steps: create a brief with `/s:initiative new <slug>`,
  attach it with `/s:initiative set <epic> <initiative>`, and tick outcomes
  with `/s:initiative review <slug>`;
- that `new` and `review` write only to the workspace and open no pull
  request, while `set` edits the epic's header and ships as a pull request;
- that an epic carries exactly one initiative, that a member derives its
  initiative through its epic, and that `set` refuses a member change;
- that a standalone change carries its own `Initiative:` line.

The `## Reference` section SHALL hold one table of the four verbs `new`,
`list`, `review`, and `set`, each with its arguments and what it writes,
and SHALL name `shipd workspace` as the roster view and
`shipd lint --initiative <slug>` as the check. The page SHALL link
`epics.md`, `workspaces.md`, and `prd.md` as the owner of the hierarchy
diagram, and SHALL carry no mermaid fence. Every command on the page SHALL
be a `/s:` skill or a `shipd` verb.

#### Scenario: Page covers where a brief lives
- **WHEN** `docs/initiatives.md` is inspected
- **THEN** it states that a brief lives in the workspace, shows the brief
  shape with `Status: open` and checkbox requirements, and names the three
  statuses

#### Scenario: Page covers the attachment rules
- **WHEN** `docs/initiatives.md` is inspected
- **THEN** it states that an epic carries one initiative, that `set` ships
  as a pull request, and that `set` refuses a member change

#### Scenario: Reference table lists the four verbs
- **WHEN** the `## Reference` section is read
- **THEN** its table holds `new`, `list`, `review`, and `set`, and the
  section names `shipd workspace` and `shipd lint --initiative <slug>`

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py` runs over `docs/initiatives.md`
- **THEN** it exits 0 with the file marked `how-to`, the file holds no
  mermaid fence and no engine script path, and every relative link resolves
