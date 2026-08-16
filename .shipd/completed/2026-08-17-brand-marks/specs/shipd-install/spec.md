## ADDED Requirements

### Requirement: Installer brand mark
id: installer-brand-mark

After a successful install, `install.sh` SHALL print its completion line with the ☕ brand mark directly before the product name — `Installed the ☕ shipd launcher at <path>` — while the PATH hint, the auto-update notice, and every failure path stay otherwise unchanged.

#### Scenario: Success line is branded
- **WHEN** `install.sh` completes successfully
- **THEN** stdout carries a completion line containing `☕ shipd launcher`

#### Scenario: Aborts stay unbranded
- **WHEN** `install.sh` aborts on a missing prerequisite
- **THEN** its output carries no `☕` mark
