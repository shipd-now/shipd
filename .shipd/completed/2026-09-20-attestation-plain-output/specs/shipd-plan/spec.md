## MODIFIED Requirements

### Requirement: Evidenced readiness attestation
id: readiness-attestation
base: 4a061d476072
Dropped: Attestation precedes emission
Dropped: An uncitable item blocks the auto-proceed

Before proceeding from investigation to emission, the `shipd:plan` skill SHALL
print a user-visible plain-language readiness attestation carrying, for each
of the four checklist items, the item's name and a one-to-two-sentence plain
statement of how it is met — stating counts and reasons (for example, how many
files are affected and why) rather than citations — followed by one closing
line naming the absolute path of the change's `plan.md`, where the full
evidence lives. The skill SHALL resolve the change name before printing, so
the named path is the real destination. The printed attestation SHALL NOT be
a markdown table and SHALL NOT reproduce the evidence citations. The emitted
`plan.md` SHALL carry a `## Readiness attestation` section with one level-3
subsection per checklist item, each holding the plain statement first and
then evidence dot-points to the unchanged citation standards: items 1–3 cite
a capability name, a `file:line` reference, or a requirement id, and item 4
names every task-shaping decision with how it was settled (investigation,
personal memory, the oracle, or the user) or states explicitly that none
remain. If an item cannot be discharged with such evidence in the staged
section, then the skill SHALL treat it as unmet and SHALL NOT proceed to
installation. The section's phrasing SHALL avoid the context gate's
placeholder markers. Internal reasoning SHALL NOT substitute for the printed
attestation or for the emitted section.

#### Scenario: Plain attestation precedes emission
- **WHEN** investigation satisfies the readiness checklist
- **THEN** before authoring any artifact the skill prints four plain-language
  headed statements and a closing line naming the absolute `plan.md` path,
  with no table and no citations in the terminal output

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

### Requirement: Premise evidence appears in the readiness attestation
id: premise-evidence-in-attestation
base: c2f65fd0b6a5
Dropped: The attestation carries the observation

The readiness checklist SHALL carry the runnable-premise rule as evidence
under its affected-capabilities-and-files item rather than as an additional
checklist item, so the four items are unchanged in number. The emitted
`plan.md`'s `## Readiness attestation` section SHALL name each verified
premise with its invocation and its observed output or exit code under that
item's evidence; the printed attestation SHALL summarize premises in plain
language without reproducing the invocations.

#### Scenario: The checklist keeps four items
- **WHEN** the readiness checklist is read after this change
- **THEN** it still gates on exactly four items

#### Scenario: The observation lands in the section
- **GIVEN** a plan that verified a runnable premise
- **WHEN** the change is emitted
- **THEN** the `## Readiness attestation` section names the premise's
  invocation and what running it showed
