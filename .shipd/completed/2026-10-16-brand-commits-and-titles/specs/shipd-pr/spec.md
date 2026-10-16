## MODIFIED Requirements

### Requirement: Title rendering
id: pr-title-render
base: 9da11755275f

`plugins/s/skills/pr/scripts/pr_title.py` SHALL render the title from the resolved `pr.title` template. The ticket SHALL come from `--ticket`, else from the first match of `pr.ticket_pattern` in the branch name. When there is no ticket, the script SHALL drop `{ticket}` and the whitespace after it. `{change}` SHALL be the slug of a `change/<slug>` branch, else empty. The script SHALL collapse repeated whitespace, and if the rendered title is empty it SHALL exit 1. The script SHALL then pass the rendered title through `spec_common.brand_subject`, so the printed title starts with `☕ Shipd: ` exactly once.

#### Scenario: Ticket from the branch
- **GIVEN** template `{ticket} {summary}`, pattern `[A-Z]+-[0-9]+`, branch `change/ABC-12-add-x`
- **WHEN** the title renders with summary `Add x`
- **THEN** it is `ABC-12 Add x`

#### Scenario: No ticket drops the placeholder
- **GIVEN** template `{ticket} {summary}` and no ticket
- **WHEN** the title renders with summary `Add x`
- **THEN** it is `Add x`

#### Scenario: Flag beats branch
- **WHEN** `--ticket XY-9` is given and the branch also matches the pattern
- **THEN** the title uses `XY-9`

#### Scenario: The printed title carries the brand once
- **WHEN** `pr_title.py title --summary "Add x"` runs
- **THEN** it prints `☕ Shipd: Add x`
- **WHEN** it runs with `--summary "☕ Shipd: Add x"`
- **THEN** it prints `☕ Shipd: Add x`
