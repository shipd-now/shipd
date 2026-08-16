## REMOVED Requirements

### Requirement: Board HTML page
id: board-html
base: 235946794a1e
Reason: The HTML page mode is unused, and its flat table had already drifted from the TUI's lane semantics (it read a member's `stage` only from the autopilot roster, ignoring the interactive build heartbeat the TUI honors).
Migration: No replacement — the board's surfaces are the interactive `tui` verb and the `board` text mode; previously written board page files are stale artifacts safe to delete, and invoking the removed verb now fails as an unknown argument (exit 2).
