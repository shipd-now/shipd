## ADDED Requirements

### Requirement: README links the workspaces guide first
id: readme-workspaces-flagship-link

The README's introduction SHALL link the workspaces guide
(`docs/workspaces.md`), and among the README's links into `docs/` that link
SHALL come first or immediately after the `docs/what-is-shipd.md` entry link.

#### Scenario: Workspaces guide is the flagship link
- **WHEN** the README's links into `docs/` are enumerated top to bottom
- **THEN** `docs/workspaces.md` is linked, preceded by no `docs/` link other
  than `docs/what-is-shipd.md`
