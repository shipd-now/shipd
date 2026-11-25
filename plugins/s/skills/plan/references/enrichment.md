<!-- doc-type: reference -->

# Enrichment mode — the loop and the re-gate

Loaded only when `/s:plan`'s `locate` finds the argument's change at status
`rejected` (see `SKILL.md`, "Enrichment mode"). Operate on the located root
for the rest of the session.

## The enrichment loop — diagnose the gaps

The change is already installed; enrichment **edits it in place** in the located
change directory (`<root>/<dir>`), never re-emitting through staging.

1. **Read the artifacts through the engine.** Load the installed change with

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" --root <root> cat change <change>
   ```

   which prints `plan.md`, every delta spec, and `tasks.md`. The plan's
   **`## Context insufficient`** section (written by the gate) is your work
   agenda: **each of its dot-points is one finding to resolve.**

2. **Resolve every codebase-answerable finding yourself, without asking.** The
   Codebase-first rule in `SKILL.md` holds in enrichment too. Resolve anything
   discoverable from the repository by editing the installed artifacts directly:
   - **Stale `base:` hash** — re-read the current master requirement (via
     `spec_status.py cat verified <capability>`). Update the delta's `base:`
     hash to the master's current hash. Reconcile the delta's content
     against what the master now says.
   - **Dangling task file references** — correct the `tasks.md` path or symbol
     to the real location in the tree. When the task creates the path, write
     Create directly before it. Never remove the backticks from a repository
     path, and never create placeholder directories, to clear the finding.
   - **Placeholder markers** (`TBD`, `???`, an undecided name) — replace them
     with a decision grounded in the repository's existing patterns.

3. **Put only the true gaps to the user.** Ask only about a finding the
   repository genuinely cannot answer. An example is an undecided product
   choice encoded as a placeholder. First route each true gap through
   the oracle rung (see "The oracle rung" in `SKILL.md`). Only the gaps it
   leaves open reach the typed round: `INSUFFICIENT` verdicts and
   `Authority: advisory` answers. Batch those under the **fast-path question
   contract**: a visible context brief first, then a plain-text numbered typed
   round. Fold the answers back into the artifacts. **Do not ask about anything
   discoverable from the repository.** An enrichment-time consultation is
   ledgered like any other. **Append** its entry to the installed `plan.md`'s
   `## Questions and answers` section, in place, like every other enrichment
   edit. **Continue the existing numbering** from the highest `Q<n>` already
   there. Create the section when the plan carries none yet.

## Exit enrichment through the re-gate

When the agenda is resolved, re-run the gate engine on the **located root** —
the gate is the only exit to `ready`:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_gate.py" <change> --root <root>
```

- **Exit 0** — the gate stripped the `## Context insufficient` section and
  promoted the change to `ready`. Confirm the change now sits at `ready`. Hand
  off with the **motivation-led summary**. Lead with the plan's
  `### Motivation`, then a brief sense of the `## Implementation`. Close with
  the `## Summary` heading and its one sentence. Then write a colon-terminated
  sentence and a blank line. Put `/s:build` alone on its own line, never inline
  mid-sentence.
- **Exit 2** — the gate re-wrote a new `## Context insufficient` section and
  parked the change back at `rejected`. Present the remaining findings and
  **continue the enrichment loop** with them as the new agenda — do not end.

**Never** move an enrichment change out of `rejected` with
`spec_status.py set-status` or `--force`. The gate's verdict is the only path
to `ready`; a forced status is a protocol violation.
