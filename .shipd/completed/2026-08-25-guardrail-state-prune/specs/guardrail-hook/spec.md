## ADDED Requirements

### Requirement: Cooldown state pruning
id: guardrail-state-prune

When the hook records remind cooldown state, then after a successful state
write it SHALL sweep the state directory and delete every regular file
matching `*.json` whose modification time is older than seven days, leaving
newer files, non-JSON entries, and subdirectories untouched. The sweep SHALL
run only on the write path — a call that fires no remind rule SHALL trigger
no sweep. If the sweep fails in any way — an unreadable directory, an
undeletable file, a file vanishing mid-sweep — then the hook SHALL ignore the
failure, keep the already-emitted reminder and the already-written state, and
exit 0. The cooldown documentation (the standalone guide's cooldown section
and the format authority's Guardrails section) SHALL state that state files
from past sessions are removed automatically about a week after their last
use.

#### Scenario: A stale session file is pruned on write
- **GIVEN** a state directory holding another session's `.json` file with a
  modification time older than seven days
- **WHEN** a remind rule fires and records state
- **THEN** the stale file is deleted and the firing session's own state file
  exists

#### Scenario: A fresh session file survives the sweep
- **GIVEN** a state directory holding another session's `.json` file with a
  recent modification time
- **WHEN** a remind rule fires and records state
- **THEN** that file still exists afterward

#### Scenario: A non-JSON entry is never touched
- **GIVEN** a state directory holding a week-old file not matching `*.json`
- **WHEN** a remind rule fires and records state
- **THEN** that entry still exists afterward

#### Scenario: No fire, no sweep
- **GIVEN** a state directory holding a stale `.json` file
- **WHEN** a PostToolUse payload matching no remind rule is evaluated
- **THEN** the stale file still exists and the script exits 0

#### Scenario: A failing sweep does not disturb the reminder
- **GIVEN** a stale state file that cannot be deleted
- **WHEN** a remind rule fires
- **THEN** the reminder is still emitted, the session's state is written, and
  the script exits 0

#### Scenario: The docs state the auto-pruning
- **WHEN** a reader consults the standalone guide's cooldown section
- **THEN** it states that past sessions' state files are removed
  automatically about a week after their last use
