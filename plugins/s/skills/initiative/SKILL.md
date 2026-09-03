---
name: initiative
description: >-
  Drive workspace initiatives through their CLIs: create a lint-clean brief from
  a workspace-first interview (new), report every initiative's status and
  requirement progress (list), walk a brief's outcomes and sync its status
  (review), or tag an epic with exactly one initiative via a PR (set). Use when
  asked to "start an initiative", "create/review a brief", "track outcomes", or
  "attach an initiative to an epic". Trigger phrases: "initiative", "brief",
  "attach an initiative", "/s:initiative".
---

# /s:initiative — Guided initiative briefs & epic attachment

You are the **Initiative steward**. Your job is to wrap the initiative,
workspace, and epic CLIs in a guided flow so briefs are authored, reviewed, and
attached without hand-editing markdown. You do **not** re-implement any check the
CLIs already own — you interview, drive the exact commands, and stop.

**The grouping layer.** An initiative sits above epics in the
Initiative → Epic → Change hierarchy. A brief captures an initiative's outcome
requirements — outcomes ticked over time, not tasks — and epics attach to it via
an `Initiative:` line. Briefs live in the **workspace**, not the repo, under the
workspace's resolved content directory (`<workspace-root>/.shipd/initiatives/<slug>/
brief.md` by default), discovered by the nearest ancestor whose `.shipd-config.json`
declares a `workspace` key. You never construct that path yourself — the engine
resolves and writes it.

Requirements: a discoverable workspace (every verb resolves one; see the
workspace-first rule). For `set`, this repo must also have the resolved
content-directory layout (epics live under its `epics/<slug>/`).

**Where to run — briefs live outside the repo, `set` edits the repo:**
- `new` and `review` affect **only** the workspace (outside the repository), so
  the repo's worktree-and-PR workflow does **not** apply. `new` installs the
  brief through `spec_emit.py initiative` (never writing the workspace path
  directly); `review` ticks outcomes and drives `initiative-sync`.
- `list` reads only; it changes nothing.
- `set` writes the epic's `Initiative:` line through the engine's
  `epic-set-initiative` verb (never hand-editing the epic), an in-repo change,
  so it ships through the repository's worktree-and-PR workflow (never a direct
  commit to `main`).

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):
- Status CLI: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (the initiative/workspace/`epic-set-initiative` verbs the flow drives)
- Emit engine: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py`
  (`initiative <slug> --from <file>` — the only way `new` writes a brief)
- Spec linter: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_lint.py`
  (a sibling skill in the same plugin — this cross-reference is intended)
- Worktree create path (for `set` only):
  `"${CLAUDE_PLUGIN_ROOT}/bin/shipd" worktree` (run from repo root)

Run the CLIs from the repo root (so `--root` may be omitted, defaulting to the
cwd); they resolve the workspace from there.

---

## Workspace-first rule (non-negotiable)

**Investigate before you ask.** Before putting a single question to the user,
resolve the workspace and read what is already there:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" workspace-show
```

This prints the workspace root, its declared project slugs, and every existing
initiative with its status and `Project:` scope. Read the existing briefs and the
declared project slugs **before** asking anything — the goal, the outcomes, and
the scope options are grounded in what you find, never guessed. A question you
could have answered by reading is a failure of this skill.

**No workspace → stop.** Every verb resolves the workspace from `--root` (the
cwd). When no workspace root is discoverable, the CLI exits non-zero with its
no-workspace error (no ancestor's `.shipd-config.json` declares a `workspace`).
**Report that error verbatim, write nothing, and stop** — never invent a
location for a brief or an epic. Then **point the user at `/s:workspace init`**
as the setup path: it creates the workspace marker so these verbs resolve.

## Verb dispatch

Parse the invocation argument into exactly one verb, then follow that verb's
section below:

- **`/s:initiative new <slug>`** → interview → author a lint-clean open brief.
- **`/s:initiative list`** → report every initiative's status and progress.
- **`/s:initiative review <slug>`** → walk outcomes, tick, then sync.
- **`/s:initiative set <epic> <initiative>`** → tag an epic via a PR.

---

## `new <slug>` — interview → lint-clean open brief

1. **Investigate** per the workspace-first rule: run `workspace-show`, read any
   existing briefs, and note the declared project slugs (candidate `Project:`
   scopes to offer).
2. **Ask one batched round** (see the question contract): the initiative's
   **goal**, its **outcome requirements** (the checkbox outcomes), and the
   **optional `Project:` scope** — offer the declared project slugs as options,
   plus "unscoped". If investigation already settled everything, ask nothing.
3. **Author the brief in a staging file** (e.g. a `mktemp` path — never the
   workspace path, which the engine owns) at `Status: open`, in this shape:

   ```
   # <slug>
   Status: open
   Project: <project-slug>    (optional — only a slug declared in the registry)

   <one or two sentences stating the initiative's goal>

   ## Requirements

   - [ ] <outcome the initiative must achieve>
   - [ ] <another outcome>
   ```

   Rules the linter enforces (get them right up front):
   - `# <slug>` title matching the directory; `Status: open` (new briefs open).
   - The only recognized metadata key is `Project:`, kebab-case, naming a
     project slug declared in the workspace registry. Omit it entirely when the
     initiative is unscoped. Where the registry declares no projects, a
     `Project:` line is an error.
   - A `## Requirements` section with **at least one** `- [ ]` checkbox. Phrase
     each as an **outcome** the initiative achieves — not a task. Emit them all
     unticked (`- [ ]`); `review` ticks them later.
4. **Install the brief through the engine** (no PR — it lands in the workspace,
   outside the repo). The emit engine resolves the workspace brief path,
   validates with the initiative checks, and on any finding removes what it
   installed and exits non-zero:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py" \
       initiative <slug> --from <staging-file>
   ```

   If it reports any finding, fix the staged brief and re-run — nothing was
   installed. Never finish `new` on a non-zero emit, and never write the brief's
   workspace path by hand.

## `list` — every initiative's status and progress

Report status without changing anything. Run `workspace-show` for the roster
(each initiative's status and `Project:` scope), then `initiative-show <slug>`
per brief for its requirement progress (the `Requirements: done/total` count and
the individual checkboxes):

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" workspace-show
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" initiative-show <slug>
```

Summarize the roster plainly: each initiative's status, its requirement
progress, and its project scope. This verb reads only — it edits nothing.

## `review <slug>` — walk outcomes, tick, then sync

1. Read the brief (via `initiative-show <slug>` and the file itself) and **walk
   its requirements with the user**, one by one — for each open (`- [ ]`)
   outcome, ask whether it is now achieved.
2. For every outcome the **user confirms achieved**, tick its checkbox in the
   brief (`- [ ]` → `- [x]`). Tick only what the user confirms; leave the rest.
3. **Sync** the derived status — this re-derives `achieved` (only when every
   requirement is ticked) or leaves it `open`, and never touches a `dropped`
   brief:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" initiative-sync <slug>
   ```

   Report the status it prints. Do not hand-write the `Status:` line — the sync
   verb owns that transition.

## `set <epic> <initiative>` — tag an epic via a PR

`set` attaches **exactly one** initiative to an epic by driving the engine's
`epic-set-initiative` verb — never hand-editing the epic file. It edits the
repo, so it ships through the worktree-and-PR workflow — never a direct commit
to `main`.

**Refusal rule (check first).** Asked to attach an initiative to a **change**
whose plan carries an `Epic:` line, **refuse**: an epic member derives its
initiative through the epic, and a plan carrying both `Epic:` and `Initiative:`
is a lint error. Name the epic as the attachment point and tell the user to run
`/s:initiative set <that-epic> <initiative>` instead. `set` targets epics only
— there is no `set` on a standalone change (a standalone plan carries
`Initiative:` via `/s:plan`).

When the target is a genuine epic, proceed:

1. **Create the worktree** for the edit from the repo root, and work inside it:

   ```
   "${CLAUDE_PLUGIN_ROOT}/bin/shipd" worktree initiative-set-<epic>
   ```

2. **Write the `Initiative:` line through the engine.** Run the header verb,
   which writes `Initiative: <initiative>` into the epic's metadata block,
   replacing any existing `Initiative:` line (exactly one per epic) and
   preserving all other header and body content:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" \
       epic-set-initiative <epic> <initiative>
   ```

   Never hand-edit the epic file — the verb owns that write.
3. **Verify with the linter's `--epic` mode** before shipping — it checks the
   epic's structure and, via the CI-safe reference rule, that the `Initiative:`
   reference resolves to a real brief in the discoverable workspace:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_lint.py" --epic <epic>
   ```

   Fix and re-run until it exits `0` and prints `OK`. Never ship on a non-zero
   lint.
4. **Ship the edit** through the repository's PR workflow: commit on the
   `change/initiative-set-<epic>` branch, push, open a PR, and let it auto-merge
   (`gh pr merge --auto --squash --delete-branch`). Report the PR with its full
   clickable URL.

## The question contract (AskUserQuestion)

`new` is the only verb that interviews; it asks under this discipline:

- **Batch into one call.** Issue a *single* AskUserQuestion covering the goal,
  the outcome requirements, and the optional `Project:` scope. Never drip
  questions one at a time.
- **Only the un-inferrable.** Every question must be a decision the workspace
  and the request cannot answer. If `workspace-show` or an existing brief
  already settled it, do not ask it.
- **Concrete options, default first.** Offer concrete options — for scope, the
  declared project slugs plus "unscoped" — with the recommended default listed
  first.
- **Ask once, then converge.** Fold the answers in and go straight to authoring
  the brief; do not spawn a fresh round unless an answer genuinely opened a new
  un-inferrable decision.

## Question rejection recovery

**Question rejection recovery.** A known Claude Code bug can deliver an
AskUserQuestion interaction as a tool rejection ("The user doesn't want to
proceed with this tool use") even when the user tried to answer. Never treat a
rejected or interrupted AskUserQuestion as a decline, a stop, or an answer.
When the user's next message arrives: if it answers the pending question, fold
it in and continue; otherwise re-offer the same choices as a plain-text
numbered list and wait for a typed reply. Only an explicitly selected or typed
stop/decline ends the flow.

## Ending — report and stop

Each verb ends the moment its work is done and self-consistent:

- **`new`** — the brief was installed via `spec_emit.py initiative` at
  `Status: open` and lints clean; report the path the engine printed and its
  requirement outcomes.
- **`list`** — the roster is reported; nothing was changed.
- **`review`** — the confirmed outcomes are ticked and `initiative-sync` has
  run; report the derived status.
- **`set`** — the epic carries the single `Initiative:` line, `--epic` lint is
  clean, and the PR is open/auto-merging; report the PR with its full URL. Or,
  on the refusal path, the epic to tag instead was named and nothing was
  written.

Then **stop** — this skill does no other work. It never plans or builds member
changes, and never writes a brief's or an epic's status by hand where a CLI verb
owns that transition.
