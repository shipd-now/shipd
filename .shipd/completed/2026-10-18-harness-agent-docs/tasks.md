## 1. The reference

- [x] 1.1 [req: agent-surface-docs] Create `docs/harness-agents-reference.md`
      with the `<!-- doc-type: reference -->` marker: a paragraph stating what
      the agent surface is and that it is gated on the `subagents` feature; a
      table naming `claude-code`, `opencode`, `agy`, and `oh-my-pi` with each
      one's agent repository pattern, user-global directory, and frontmatter; a
      section naming the `shipd-sub-agent`, `shipd-oracle`, and
      `shipd-validator` ids and what each role does; and a short section on
      adding a harness (a new registry entry with an `agent` member, then
      `shipd harness add`). Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/harness-agents-reference.md`
      and fix every finding.

## 2. Customise points at it

- [x] 2.1 [req: agent-surface-docs] In `docs/customise.md`, extend the
      `## The harness` section: one sentence naming the agent files a harness
      receives beside its commands and that only a harness declaring
      `subagents` gets them, and a link to `harness-agents-reference.md`. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/customise.md`
      and fix every finding.

## 3. Verify

- [x] 3.1 [req: *] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/customise.md docs/harness-agents-reference.md`
      and confirm it exits 0. Run
      `python3 plugins/s/skills/build/scripts/spec_lint.py harness-agent-docs`
      and confirm it prints `OK`. Confirm every claim in the reference against
      `python3 plugins/s/skills/build/scripts/spec_status.py cat verified harness-registry`
      — the four agent patterns, user dirs, and frontmatter.
