## REMOVED Requirements

### Requirement: Copilot setup skill flow
id: copilot-skill-flow
base: b69211411357
Reason: The skill is renamed `/s:gate` — the handle names the merge gate, provider-neutrally, not the Copilot backend behind it.
Migration: Continues verbatim (paths, trigger, and fallback branch updated) as `gate-skill-flow` in the `shipd-gate` capability.

### Requirement: Copilot skill registration
id: copilot-skill-registration
base: 614f4b7a01b4
Reason: The skill is renamed `/s:gate`; its registration surfaces move with it.
Migration: Continues (paths and trigger updated) as `gate-skill-registration` in the `shipd-gate` capability.
