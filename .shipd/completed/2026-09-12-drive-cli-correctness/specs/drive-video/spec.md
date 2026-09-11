## ADDED Requirements

### Requirement: The action-module reference matches the helper
id: drive-helper-docs

The action-module reference `references/recording.md` SHALL document the
helper object `h` with the method names, parameter names, and parameter order
that `record_worker.py`'s `Helper` actually defines, so an action module
written from the reference runs unchanged. The reference SHALL NOT present as
part of the helper's API any `h.<name>` that `Helper` does not define. The
repository SHALL carry a test that resolves every helper name the reference
documents against `Helper` through runtime signature inspection, and that test
SHALL fail when a documented name is absent from the implementation, when a
documented parameter name is absent from that method's signature, or when the
documented parameters appear in an order the real signature does not have.

#### Scenario: Every documented helper method exists
- **WHEN** the doc-drift test inspects `Helper` for each method the reference
  documents
- **THEN** every documented method name resolves on `Helper`

#### Scenario: Documented parameter names match the implementation
- **WHEN** the test compares each documented method's parameter names against
  the signature `Helper` defines
- **THEN** every documented parameter name appears in that signature

#### Scenario: Documented parameter order matches the implementation
- **WHEN** the reference documents a method's parameters in an order the real
  signature does not declare
- **THEN** the doc-drift test fails and names that method

#### Scenario: A documented name that is not a helper member fails the test
- **WHEN** the reference presents an `h.<name>` that `Helper` defines neither
  as a method nor as an attribute
- **THEN** the doc-drift test fails and names it

#### Scenario: A renamed helper method fails the test
- **WHEN** a helper method the reference documents is renamed in
  `record_worker.py` without the reference being updated
- **THEN** the doc-drift test fails and names the missing method
