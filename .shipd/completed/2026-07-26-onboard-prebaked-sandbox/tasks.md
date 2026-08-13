## 1. Template assets

- [x] 1.1 [req: sandbox-template] Create
      `plugins/s/skills/onboard/assets/sandbox/` holding the sandbox `.shipd/`
      layout: `verified/.gitkeep` (empty master library) and
      `planned/add-board/` with the pre-authored cycle-1 artifacts —
      `plan.md` (`# add-board`, `Status: draft`, `## Idea` motivating a way
      to see cards with a `### Non-goals` excluding add/edit, and
      `## Implementation` naming `kanban.py` + `cards.json`);
      `specs/kanban/spec.md` (`## ADDED Requirements` declaring `list-cards`
      — the CLI SHALL list every card with id, lane, and title — and
      `board-view` — the CLI SHALL render cards as a three-column
      todo/doing/done board — each with an `id:` and one `#### Scenario:`);
      `tasks.md` (three unchecked checklist tasks — implement `list`,
      implement `board`, seed `cards.json` — each carrying the req tag of
      the requirement it implements: list-cards, board-view, and both,
      respectively).
- [x] 1.2 [req: sandbox-template] Create
      `plugins/s/skills/onboard/assets/solutions/add-board/` with the
      reference implementation: `kanban.py` (stdlib-only python3; `list`
      subcommand printing `#<id> [<lane>] <title>` per card; `board`
      subcommand printing three columns headed TODO / DOING / DONE with card
      titles under their lanes; cards loaded from `cards.json` beside the
      script) and `cards.json` (three cards spread across the three lanes).

## 2. Skill update

- [x] 2.1 [req: sandbox-template] In
      `plugins/s/skills/onboard/SKILL.md`, rewrite the scaffold and cycle-1
      sections: scaffold copies
      `${CLAUDE_PLUGIN_ROOT}/skills/onboard/assets/sandbox/` into `$SANDBOX`
      and runs `git init` (no live authoring, and an explicit rule never to
      read the user's real repository for example shapes — the template is
      the example); cycle 1 is structured as three checkpointed beats, each
      opened by a one-or-two-sentence statement of what is about to happen —
      beat A: orient and walk the pre-authored `add-board` artifacts in short
      excerpts, then pause with a typed prompt; beat B: lint, promote to
      `ready`, copy the `assets/solutions/add-board/` files into the sandbox
      as the build step, run `python3 kanban.py board` to show the payoff,
      then pause; beat C: tick tasks, drive complete/verified, merge, and
      close with a few-sentence lifecycle explanation at the cycle
      checkpoint.
- [x] 2.2 [req: walkthrough-pacing] In the same file, add a "Pacing" section
      and weave its rules into the cycles and guardrails: explain before
      doing (a sentence or two of intent ahead of every action — never a
      silent batch of steps explained retrospectively); pause at beat
      boundaries with plain-text typed prompts so no cycle completes without
      a user reply; teach in short beats (a few short paragraphs per turn,
      never a recap essay); quote files only as short excerpts; show the
      rendered board early in cycle 1; cap post-merge lifecycle explanations
      at a few sentences; never narrate internal troubleshooting or
      command-syntax discovery — the engine invocations documented in the
      skill are authoritative and used as written.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.3.4 → 0.3.5.
- [x] 3.2 [req: *] Smoke-verify the template end-to-end: copy
      `assets/sandbox/` to a `mktemp -d` sandbox, `git init`, run
      `spec_lint.py add-board --root` (must print OK), promote to `ready`,
      copy in the `assets/solutions/add-board/` files, confirm
      `python3 kanban.py board` renders the three-lane board with the sample
      cards and `list` prints one line per card, tick all tasks via
      `claim_task.sh`, drive `complete` → `verified`, merge with
      `spec_merge.py`, and confirm `verified/kanban/spec.md` was seeded and
      the change archived. Then delete the smoke sandbox.
