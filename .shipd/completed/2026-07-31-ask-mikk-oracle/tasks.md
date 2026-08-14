# Tasks

## 1. Oracle agent definition

- [x] 1.1 [req: oracle-agent-contract, oracle-cited-answers, oracle-insufficient-queue, compact-question-contract]
      Write `plugins/s/agents/oracle.md` following the frontmatter/body shape
      of `plugins/s/agents/validator.md`: `name: oracle` plus a one-line
      `description:`; a role statement (non-interactive oracle, never asks the
      user, never blocks the caller); the spawn inputs (one compact question —
      decision, options, recommendation — plus the asking repo's absolute
      root); the binding search ladder with exact commands
      (`spec_status.py wiki-show`, `cat wiki index`, `cat wiki <slug>`,
      read-only grep under `<ws-root>/<content-dir>/wiki/`, then
      `spec_status.py --root <asking-root> cat verified|epic|research` and
      `project-show`); the verdict contract (first non-blank line exactly
      `ANSWER` or `INSUFFICIENT`; `ANSWER` = one recommended position plus
      `Cited:` lines; `INSUFFICIENT` = the compact question block plus a
      `Queued:` line); the queue behavior (read `cat wiki queue` first and
      cite an equivalent pending question instead of duplicating; otherwise
      `wiki-queue-add <q-slug> --question --options --recommendation --origin
      <asking-repo>`; run `wiki-init` first when the store is missing; report
      `Queued: none` naming the missing workspace when none is discoverable);
      and guardrails (store writes only via `wiki-queue-add`/`wiki-init`,
      never edit wiki files directly, never touch the asking repo's files).

## 2. Ask skill

- [x] 2.1 [req: ask-skill, compact-question-contract] Write
      `plugins/s/skills/ask/SKILL.md` in the house skill shape (frontmatter
      `name: ask` with a trigger-phrase `description:`, per
      `plugins/s/skills/research/SKILL.md`): announce `am:ask v<version>`
      read from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`; shape the
      user's request into one compact question (decision, concrete options,
      recommendation inferred from the request and repo context — no
      interview round); spawn the oracle via the Agent tool with
      `subagent_type: s:oracle`, passing the compact question and the repo
      root; then relay the verdict — the cited `ANSWER` verbatim, or the
      `INSUFFICIENT` outcome with its `q-<slug>` and a note that answering
      the queue entry feeds the wiki (drained later by teach-mikk).

## 3. Roster, version, and cross-check

- [x] 3.1 [req: *] In `AGENTS.md`, extend the skill roster sentence in the
      "Spec layout and lifecycle" section with `/s:ask` (query the ask-mikk
      oracle before interrupting the user), keeping the existing sentence
      style.
- [x] 3.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.6 to 0.6.7.
- [x] 3.3 [req: *] Cross-check the two new files against the delta: grep
      `plugins/s/agents/oracle.md` and `plugins/s/skills/ask/SKILL.md` for
      the `ANSWER`/`INSUFFICIENT` first-line contract, the
      decision/options/recommendation compact-question shape, and the
      `wiki-queue-add`/`wiki-init` queue path; fix any drift so both files
      state all three.
