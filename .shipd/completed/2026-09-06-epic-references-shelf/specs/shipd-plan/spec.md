## ADDED Requirements

### Requirement: Supplied document install and link
id: plan-supplied-document-install

Where the user supplies a context document for the change that does not
already reside under the content directory's `research/`, `video/`, or
`docs/` folder, the `/s:plan` skill SHALL install it through
`spec_emit.py docs <slug> --from <file>` — never by writing into the spec
tree directly — choosing a kebab-case slug derived from the document's
level-1 title, or from its filename when the document carries no title, and
staging a titled copy when the document's first line is not a level-1 title,
leaving the user's original file unmodified. The skill SHALL read the
installed document as investigation input. When the change carries an
`Epic:` header resolving to an epic in the repository, the skill SHALL link
the installed document from that epic's `## References` section, creating
the section when absent; when the change carries no resolving epic, the
skill SHALL cite the installed document in `plan.md` prose and SHALL edit no
epic. A supplied file already residing under one of the three folders SHALL
be read without reinstalling.

#### Scenario: A supplied document is installed and shelved
- **GIVEN** planning for a change whose plan carries `Epic: <slug>` and a
  user-supplied strategy document outside the content directory
- **WHEN** the plan is emitted
- **THEN** the document is installed at the resolved `docs/<slug>/doc.md`
  via the emit engine and the epic's `## References` section links it

#### Scenario: An epic-less plan cites without shelving
- **GIVEN** planning for a standalone change with no `Epic:` header and a
  user-supplied document
- **WHEN** the plan is emitted
- **THEN** the document is installed through the docs kind, `plan.md` cites
  it, and no epic file is edited

#### Scenario: An already-installed file is not reinstalled
- **GIVEN** the user points planning at a file already under the content
  directory's `docs/` folder
- **WHEN** planning proceeds
- **THEN** no install runs and the file is read as investigation input
