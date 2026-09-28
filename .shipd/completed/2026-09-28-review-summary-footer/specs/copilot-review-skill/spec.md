## ADDED Requirements

### Requirement: Copilot skill clean-verdict wording
id: copilot-clean-wording

The Copilot review skill template SHALL instruct the reviewing agent to write `No problems found.` in place of the severity summary table when the review carries no findings, SHALL state that the gate workflow's posting step closes the posted body with the `Reviewed N files, +A -D lines.` stat line, and SHALL instruct the agent not to write that line itself. The template SHALL NOT carry the retired `No findings.` sentence.

#### Scenario: The template mandates the wording
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` is read
- **THEN** it contains `No problems found.`, contains `Reviewed N files, +A -D lines.`, and does not contain `No findings.`

### Requirement: Gate workflow posted-body footer
id: gate-body-footer

Where the gate's own reviewer produced the review, the review-gate workflow's posting step SHALL append one stat line, `Reviewed N files, +A -D lines.`, to the body it posts, counted from the changed-files read that step performs itself, and SHALL fold it above the verdict marker so the marker remains the last line equal to a marker. The line's format SHALL match `review_footer` in `review_gate.py` for every file list, including the singular noun, the count-less form, and the empty list, so a review reads the same whichever surface posted it. When the changed-files read failed, no footer SHALL be appended.

#### Scenario: Workflow footer matches the poster
- **WHEN** the posting step's `footer` function is executed from the workflow source against a file list
- **THEN** it returns an empty block when `review_footer` returns none, and otherwise a block whose last line equals `review_footer`'s line

#### Scenario: Footer stays above the marker
- **WHEN** the posting step folds the footer into a body ending in a verdict marker
- **THEN** the marker is still the body's last non-blank line

#### Scenario: Unreadable diff appends nothing
- **WHEN** the changed-files file is empty or not a list
- **THEN** the posting step appends no `Reviewed` line
