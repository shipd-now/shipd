---
name: worktree-hooks
description: >-
  Author and register the setup scripts a new worktree runs: turn a described
  setup need into an executable script under `<content-dir>/hooks/`, register
  its repo-relative path through the binary's `worktree hooks add` verb, and
  verify the registration by reading `worktree hooks list` back. Also browses
  the registered hooks (flagging any whose script file is missing) and removes
  one on confirmation. Use when asked to "run something after creating a
  worktree", "set up new worktrees automatically", "copy my .env into every
  worktree", "seed the database in new worktrees", or to list/remove the
  configured post-worktree scripts. Trigger phrases: "worktree hook",
  "post-worktree script", "set up new worktrees", "run this in every worktree",
  "/s:worktree-hooks".
---

# /s:worktree-hooks — set up what a fresh worktree needs

You are the **authoring layer over the engine's `post-worktree-scripts`**. A
fresh worktree often needs repo-specific setup — a `.env` copied in, a database
seeded, dependencies installed — and the engine's worktree create path runs the
repo's configured `post-worktree-scripts` right after it creates one. Your job
is to turn a described setup need into an entry on that list: author the script,
register it through the binary, and prove the registration.

**You never hand-edit `.shipd-config.json`.** Registration and removal go
through `worktree hooks add` / `worktree hooks remove` — the verbs own the
file's format, the duplicate refusal, the shadowing warning, and the
preservation of every unrelated key. Editing the config directly bypasses all
of that, so you never do it, not even "just this once" to fix an ordering.

**Hooks are checked in.** The script lives in the repo checkout under
`<content-dir>/hooks/`, is committed like any other repo content, and is
code-reviewed like any other repo content — which is what makes it safe for the
engine to run it. It is deliberately *not* relocated by `store_root`: a hook
that lived in an external store would not travel with a checkout, and the
create path would find nothing to run.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`shipd:worktree-hooks v<version>` in your first user-visible status sentence
(e.g. "shipd:worktree-hooks v0.6.174 — registering the .env hook"), so the user
can always see which plugin snapshot the session is running.

An **invocation argument** carries what the user wants: a setup step to add
("copy .env.example into every new worktree"), a request to see what is
registered ("list the hooks"), or one to remove ("drop the db-seed hook"). When
it is absent, ask which of the three they want and wait.

## 1. Resolve the binary and the content directory

Resolve the `shipd` binary in this order and use the first that exists:

1. `shipd` on `PATH` — the consumer launcher (`command -v shipd`).
2. `${CLAUDE_PLUGIN_ROOT}/bin/shipd` — the checkout or cache-snapshot copy.

If neither resolves, report that the `shipd` binary cannot be found, name both
locations you tried, and stop. Do not install a launcher, and do not fall back
to editing the config by hand.

Then resolve the **content directory name** — it is configurable, so never
assume `.shipd`:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" \
  --root <repo-root> config-show
```

Take the name from the `dir = "<name>"` line. Hooks live at
`<repo-root>/<name>/hooks/`, **in the checkout** — even where `config-show`
reports a `store_root` relocating the rest of the content directory. The store
line is not your path; the `dir` name is.

Every `worktree hooks` verb below runs as `<shipd> worktree hooks <verb …>`
with `<repo-root>` as the working directory.

## 2. Setup flow — author, register, verify

When the user described a setup step, decide first **whether it needs a script
file at all**:

- **A plain one-line command** — `npm install`, `cp .env.example .env`,
  `docker compose up -d` — registers directly as that command line. Author no
  file; go straight to registration.
- **Anything else** — several steps, conditionals, a guard against re-running,
  anything that wants a comment — is authored as a script file.

### 2a. Author the script

Write it to `<repo-root>/<content-dir>/hooks/<slug>.sh`, where `<slug>` is a
kebab-case name for the step (`copy-env`, `seed-db`, `install-deps`). Create the
`hooks/` directory if it is absent. The script:

- starts with `#!/usr/bin/env bash` and `set -e`;
- runs with the **new worktree as its working directory**, so relative paths are
  worktree-relative;
- may read `SHIPD_WORKTREE` (the new worktree's absolute path), `SHIPD_ROOT`
  (the repo root) and `SHIPD_CHANGE` (the change name) from the environment —
  the create path exports all three;
- is **idempotent where it can be**: `hooks run` re-runs the whole list inside
  an existing worktree, so a step that would break on a second run should guard
  itself;
- **exits non-zero on failure**. The create path stops the chain at the first
  failure and exits `3`, leaving the worktree in place — so a real failure must
  be a real non-zero exit, never a warning the script swallows.

Then mark it executable:

```
chmod +x <repo-root>/<content-dir>/hooks/<slug>.sh
```

Show the user the script you wrote before registering it.

### 2b. Register it

Register the **repo-relative path** (not an absolute one — the config is
checked in and has to work in every clone and every worktree):

```
<shipd> worktree hooks add "<content-dir>/hooks/<slug>.sh"
```

or, for the one-liner case, the command line itself:

```
<shipd> worktree hooks add "npm install"
```

Handle the verb's two non-silent outcomes:

- **Non-zero exit naming a duplicate** — the item is already registered. Report
  that, register nothing further, and stop.
- **A `WARNING:` line about shadowing** — an outer config layer (a workspace
  root) declared its own list, and this repo's new list now wins the key
  *wholesale* rather than extending it. Relay that warning to the user
  verbatim and name the outer file, so they can decide whether the outer
  layer's items need re-adding here.

### 2c. Verify

Read the registration back and show it:

```
<shipd> worktree hooks list
```

Confirm the new item appears, at which index, and from which config file. If it
does not appear, report that the registration did not take and stop — never
declare success off the `add` command's own output alone.

Finish by telling the user the hook is **not yet committed**: it takes effect
for everyone once `<content-dir>/hooks/<slug>.sh` and `.shipd-config.json` are
committed, and it runs on the next `shipd worktree <change>`.

## 3. Browse flow — list what is registered

When the user asked what is registered:

```
<shipd> worktree hooks list
```

Report each item with its index and the config file that declared it. Then
**flag every dangling script**: for each item that looks like a path into
`<content-dir>/hooks/` (rather than a shell command line), check whether the
file exists in the checkout, and mark the ones that do not — a registered hook
whose script was deleted fails the create path with exit `3` on the next
worktree. Offer to remove a dangling entry (through the removal flow below); do
not remove it unprompted.

When nothing is registered, say so and offer the setup flow.

## 4. Removal flow — name it, confirm, then remove

Removal changes what every future worktree runs, so it always goes through a
**single AskUserQuestion** before any `worktree hooks remove` runs.

1. **Locate the entry.** Run `<shipd> worktree hooks list` and match the user's
   description against the items. Exactly one match proceeds; no match is
   reported as "nothing registered matches that" with the listing shown, and
   removes nothing; more than one match is presented to the user to pick from
   before you continue.
2. **Confirm.** Issue the AskUserQuestion in a **prose-free turn** — the matched
   item, its index, and its declaring config file ride inside the dialog's
   fields, not in surrounding chat prose (the dialog-and-prose-separation
   rule). Offer "Remove it" and "Keep it" (the default). Where the entry points
   at a script under `<content-dir>/hooks/`, offer the file deletion as its own
   choice — "Remove the registration and delete the script file" versus
   "Remove the registration, keep the file" — so the user consents to the
   deletion separately.
3. **On the affirmative selection**, and only then:

   ```
   <shipd> worktree hooks remove "<item>"
   ```

   (an index also works: `<shipd> worktree hooks remove 0`). If it exits
   non-zero, surface the error and report that nothing was removed. **Delete the
   script file only when** the entry pointed at one under
   `<content-dir>/hooks/` *and* the user chose that in step 2 — never as a side
   effect of the registration removal.
4. **On the negative selection** — run nothing; report that the hook was kept
   and stop.

Then read `<shipd> worktree hooks list` back and show the remaining list.

## Question rejection recovery

**Question rejection recovery.** A known Claude Code bug can deliver an
AskUserQuestion interaction as a tool rejection ("The user doesn't want
to proceed with this tool use") even when the user tried to answer.
Never treat a rejected or interrupted AskUserQuestion as a decline, a
stop, or an answer. When the user's next message arrives: if it answers
the pending question, fold it in and continue; otherwise re-offer the
same choices as a plain-text numbered list and wait for a typed reply.
Only an explicitly selected or typed stop/decline ends the flow.

## Boundaries

- **You never create or remove a worktree.** That is `shipd worktree <change>`
  and `worktree.sh remove`, run by the build flows. You only configure what
  runs after a creation.
- **You never run the hooks to "test" them against a live worktree you
  created.** To exercise a registered list in place, the user runs
  `<shipd> worktree hooks run` from inside an existing worktree; say so rather
  than creating a throwaway worktree yourself.
- **You never edit `.shipd-config.json`, `worktree.py`, or `worktree.sh`.**

## End

Report the outcome in one or two lines: what you registered, browsed, or
removed; the config file it lives in; and the files the user still has to
commit. Then stop.
