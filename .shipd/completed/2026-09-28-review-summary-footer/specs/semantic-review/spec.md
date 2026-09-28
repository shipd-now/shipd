## ADDED Requirements

### Requirement: Summary comment clean-verdict wording
id: summary-clean-wording

When a review carries no findings, `review_gate.py post` SHALL render `No problems found.` in place of the findings table, and the review skill's report rules SHALL instruct the same sentence, so a clean review reads identically from either surface. The sentence SHALL be defined once, as the `NO_PROBLEMS` constant in `review_gate.py`, and the retired `No findings.` sentence SHALL appear on neither surface.

#### Scenario: Clean review says no problems found
- **WHEN** the summary body is rendered for a review JSON whose `findings` list is empty
- **THEN** the body carries `No problems found.` below the effort line, carries no `| # |` table header, and carries no `No findings` text

#### Scenario: The skill body quotes the constant
- **WHEN** `plugins/s/skills/review/SKILL.md` is read
- **THEN** it contains `No problems found.` and does not contain `No findings.`

### Requirement: Summary comment review footer
id: summary-review-footer

`review_gate.py post` SHALL close the summary comment it upserts with one stat line, `Reviewed N files, +A -D lines.`, where N is the number of entries in the pull request's file list and A and D are the sums of those entries' integer `additions` and `deletions`. The footer SHALL be the body's last line on every verdict, after any "Additional findings" section, on the first upsert and on the folded re-post alike. When no entry carries an integer count the line SHALL read `Reviewed N files.`; when N is 1 the noun SHALL be singular; when the file list is empty or absent no footer SHALL be rendered. A boolean SHALL NOT count as a line count.

#### Scenario: Footer closes a clean summary
- **GIVEN** a pull request whose file list holds two entries with 12/3 and 100/0 additions/deletions
- **WHEN** `post` publishes a review with no findings
- **THEN** the summary body's last non-blank line is `Reviewed 2 files, +112 -3 lines.` and `No problems found.` precedes it

#### Scenario: Footer follows the folded findings
- **GIVEN** a review with one unanchored medium finding and the same file list
- **WHEN** the summary body is rendered
- **THEN** the "Additional findings" section appears before the footer and the footer is the last non-blank line

#### Scenario: Footer survives the folded re-post
- **GIVEN** the inline review POST is rejected once
- **WHEN** `post` folds the findings and re-upserts the summary
- **THEN** the re-posted body still ends with the footer

#### Scenario: Singular file and missing counts
- **WHEN** the file list holds one entry carrying no `additions` or `deletions`
- **THEN** the footer reads `Reviewed 1 file.`

#### Scenario: No file list, no footer
- **WHEN** `render_summary` is called with `files` omitted, empty, or holding no dict entries
- **THEN** the body carries no `Reviewed` line
