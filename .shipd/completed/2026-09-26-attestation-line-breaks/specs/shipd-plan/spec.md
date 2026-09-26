## MODIFIED Requirements

### Requirement: Evidenced readiness attestation
id: readiness-attestation
base: 565cc2225aa0

Before proceeding from investigation to emission, the `shipd:plan` skill SHALL
print a user-visible plain-language readiness attestation carrying, for each
of the four checklist items, the item's name and a one-to-two-sentence plain
statement of how it is met — stating counts and reasons (for example, how many
files are affected and why) rather than citations — followed by one closing
line naming the absolute path of the change's `plan.md`, where the full
evidence lives. Each of the four statements SHALL be separated from the next,
and from the closing line, by a blank line, so every statement renders as its
own paragraph in a markdown terminal rather than folding into one. The skill
SHALL resolve the change name before printing, so the named path is the real
destination. The printed attestation SHALL NOT be a markdown table and SHALL
NOT reproduce the evidence citations. The emitted `plan.md` SHALL carry a
`## Readiness attestation` section with one level-3 subsection per checklist
item, each holding the plain statement first and then evidence dot-points to
the unchanged citation standards: items 1–3 cite a capability name, a
`file:line` reference, or a requirement id, and item 4 names every
task-shaping decision with how it was settled (investigation, personal
memory, the oracle, or the user) or states explicitly that none remain. If an
item cannot be discharged with such evidence in the staged section, then the
skill SHALL treat it as unmet and SHALL NOT proceed to installation. The
section's phrasing SHALL avoid the context gate's placeholder markers.
Internal reasoning SHALL NOT substitute for the printed attestation or for
the emitted section.

#### Scenario: Plain attestation precedes emission
- **WHEN** investigation satisfies the readiness checklist
- **THEN** before authoring any artifact the skill prints four plain-language
  headed statements and a closing line naming the absolute `plan.md` path,
  with no table and no citations in the terminal output

#### Scenario: Each statement starts its own paragraph
- **WHEN** the skill prints the attestation
- **THEN** a blank line separates each of the four statements from the next
  and from the closing line, so "Scope and non-goals" begins on a new line
  of its own rather than continuing the previous statement's paragraph

#### Scenario: Full evidence lands in the emitted plan
- **WHEN** the change is emitted
- **THEN** its `plan.md` carries a `## Readiness attestation` section with,
  per checklist item, the plain statement above evidence dot-points citing a
  capability name, a `file:line` reference, or a requirement id

#### Scenario: An item without evidence blocks installation
- **WHEN** a checklist item carries no evidence dot-point in the staged
  section
- **THEN** the skill treats the item as unmet and does not install the change

#### Scenario: Item four names how each decision was settled
- **WHEN** the oracle settled one decision and the user settled another
- **THEN** the section's fourth subsection names both decisions and their
  settling rungs rather than asserting that nothing needed deciding
