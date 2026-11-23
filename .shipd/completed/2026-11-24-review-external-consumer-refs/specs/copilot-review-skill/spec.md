## ADDED Requirements

### Requirement: Copilot skill reads external consumers at a named ref
id: copilot-external-consumer-refs

The Copilot review skill template at
`plugins/s/integrations/copilot/SKILL.md` SHALL state, in its downstream-impact
section, that a consumer in another repository is never judged from its
default branch alone. It SHALL direct the reviewer to read that consumer with
an explicit `?ref=<commit id>`, first at the head of each pull request GitHub
cross-references on the reviewed one, then at the default branch. It SHALL
state that a head migrating the consumer means no finding, and that a failed
lookup means the reviewer says it could not verify that consumer and raises
nothing blocking for it.

#### Scenario: The template carries the rule
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` is read
- **THEN** its `### 3. Check downstream impact` section names a consumer in
  another repository, the `?ref=` read, and the issue timeline call

#### Scenario: A failed lookup never blocks
- **WHEN** that section is read
- **THEN** it states that a failed lookup is reported as not verified and
  raises nothing blocking
