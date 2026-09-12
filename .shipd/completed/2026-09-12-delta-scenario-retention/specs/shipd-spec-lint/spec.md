## ADDED Requirements

### Requirement: MODIFIED scenario retention
id: modified-scenario-retention

The linter SHALL refuse a change whose `## MODIFIED Requirements` entry omits
a `#### Scenario:` title its base master requirement carries, unless the entry
names that title in a `Dropped:` line. Because a MODIFIED entry replaces the
master requirement's content wholesale, an unnamed omission deletes that
scenario on merge, so the linter SHALL report one error per omitted title,
naming the requirement id and each title. The linter SHALL match scenarios by
exact title text, so rewording a scenario's body in place is never reported.
If a `Dropped:` line names a title the base requirement does not carry, then
the linter SHALL report that as an error too, so a stale or misspelled line
never appears to license an omission it does not. Where a MODIFIED entry's
`id` has no matching master requirement, the linter SHALL skip this check for
that entry, since there are no base scenarios to retain.

#### Scenario: A silently dropped scenario is refused
- **GIVEN** a master requirement carrying four scenarios
- **WHEN** a MODIFIED entry for it restates two of them and carries no
  `Dropped:` line
- **THEN** the linter reports an error naming the requirement id and the two
  omitted scenario titles, and exits non-zero

#### Scenario: A named drop is allowed
- **GIVEN** a master requirement carrying four scenarios
- **WHEN** a MODIFIED entry restates three of them and carries a `Dropped:`
  line naming the fourth
- **THEN** the linter reports no retention finding

#### Scenario: Rewording a scenario body is not a drop
- **WHEN** a MODIFIED entry restates every scenario title its base carries but
  changes the WHEN/THEN text of one
- **THEN** the linter reports no retention finding

#### Scenario: A stale Dropped line is refused
- **WHEN** a MODIFIED entry carries a `Dropped:` line naming a title its base
  requirement does not carry
- **THEN** the linter reports an error naming that title and exits non-zero

#### Scenario: A MODIFIED entry with no master is skipped
- **WHEN** a MODIFIED entry's `id` matches no requirement in the master library
- **THEN** the linter reports no retention finding for that entry
