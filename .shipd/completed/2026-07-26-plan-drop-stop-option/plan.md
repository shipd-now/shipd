# plan-drop-stop-option
Status: verified

## Idea

The findings checkpoint's typed go-ahead prompt offers three options:
proceed, adjust scope, stop here. The stop option is dead weight: with a
typed prompt, not replying (or saying anything else) already stops the flow —
nobody deliberately picks "throw away the investigation" from a menu. The
user asked for its removal.

Fix: the go-ahead prompt offers exactly two options — **1. proceed to the
depth gate and planning** (recommended, named first) and **2. adjust scope
first**. Stopping stays what it naturally is: the user simply not continuing.

### Non-goals

- No other change to the checkpoint contract: digest-first ordering, the
  no-AskUserQuestion rule, the no-planning-decisions rule, and the
  no-gate-verdict rule are untouched.

Affected capabilities: `shipd-plan` (modified — `investigation-findings-digest`).
Impact: `plugins/s/skills/plan/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Drop option 3 everywhere it is named:** the requirement's options list
  ("proceed … adjust scope first, or stop") and its no-planning-decisions
  scenario ("proceeding, adjusting scope, or stopping"), and SKILL.md step
  2's numbered prompt (including the "on stop, end politely" follow-up,
  which loses its referent).
- **Version bump to 0.2.15** in `plugins/s/.claude-plugin/plugin.json`,
  same PR, per the cache-snapshot rule in AGENTS.md.

Risks: none — a strict narrowing of an existing prompt; an explicit typed
"stop" from a user still just works, it is merely no longer advertised.
