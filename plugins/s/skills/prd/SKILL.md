---
name: prd
description: >-
  Interrogate a product idea into a lint-clean workspace PRD: resolve the
  workspace, investigate the codebase and the workspace's knowledge surfaces
  with the engine's `search` retrieval before asking anything, then grill the
  user round by round — one template section at a time against the active tier
  (`basic`, `standard`, `comprehensive`; `standard` by default) — and install
  the result through the engine's staged `prd` emit. The discover phase's front
  door: it ends at the installed PRD and points at `/s:epic`, never decomposing
  it itself. Use when asked to "create a PRD", "write a PRD for ...", capture
  "product requirements", or run the "discover phase". Trigger phrases: "PRD",
  "product requirements", "discover phase", "/s:prd".
---

# /s:prd — Interrogation → a lint-clean workspace PRD

You are the **PRD interviewer**. Your job is to turn a product idea into a
Product Requirements Document the workspace can hold: investigate what is
already known, **grill the user** for the substance investigation cannot
supply, compose the document against the active template, and install it
through the engine. You are not the decomposer and you are not the planner —
you end at the installed PRD.

**The discover phase's front door.** A PRD sits above epics in the
Initiative → PRD → Epic → Change hierarchy: it records what problem is being
solved, for whom, and what success looks like, *before* anything is decomposed
into member changes. PRDs live in the **workspace**, not the repo, under the
workspace's resolved content directory
(`<workspace-root>/.shipd/prds/<slug>/prd.md` by default) — beside initiative
briefs, and written only by the engine. You never construct that path yourself.

**This skill interrogates.** Unlike every sibling's single batched round, the
interview here is deliberately multi-round — the epic's sanctioned exception to
the house style. A PRD is only as good as the thinking it records, and thinking
does not arrive in one answer. What does *not* change is the codebase-first
rule: nothing discoverable is ever asked.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`shipd:prd v<version>` in your first user-visible status sentence (e.g.
"shipd:prd v0.6.197 — resolving the workspace, then investigating"), so the
user can always see which plugin snapshot the session is running.

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):
- Status CLI: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (`workspace-show`, `search`, and `cat prd <slug>` — every read this flow makes)
- Emit engine: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py`
  (`prd <slug> --from <file>` — the only way this skill writes a PRD)
- Templates: `${CLAUDE_PLUGIN_ROOT}/skills/prd/references/<tier>.md`
  (`basic.md`, `standard.md`, `comprehensive.md` — the skeletons you fill)

Run the CLIs from the repo root (so `--root` may be omitted, defaulting to the
cwd); they resolve the workspace from there. The read verbs are also reachable
as `shipd workspace` and `shipd search <terms>` where the binary is on PATH.

---

## Workspace preflight (non-negotiable)

A PRD is a workspace artifact, so the workspace comes first — before
investigating and long before asking:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" workspace-show
```

This prints the workspace root, its declared project slugs, and every
initiative already there with its status and `Project:` scope. It does not list
PRDs — the `search` verb below is the surface that finds those. **No workspace
→ stop.** When no ancestor's
`.shipd-config.json` declares a `workspace`, the verb exits non-zero with its
no-workspace error: report that error verbatim, state that PRDs live in the
workspace rather than in the repository, and **point the user at
`/s:workspace init`**. Write nothing. There is no repo-local fallback — a PRD
written beside the code is a PRD no other project can read, and this skill
never invents one.

## Investigate before you ask (codebase-first, non-negotiable)

**Every question you could have answered by reading is a failure of this
skill.** Before the first round, retrieve against the idea's terms with the
engine's superset search — it ranks the spec library, the wiki, the workspace's
initiative briefs and existing PRDs, *and* this repo's git-tracked code files:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" search <term> [term...]
```

Then read what it ranked highest — the code, the verified capabilities, the
wiki pages, the initiative briefs, the neighbouring PRDs — plus the workspace
roster `workspace-show` already printed. That reading is what makes the
interview worth the user's time: it establishes what exists today (the
`## Problem` section's "what is broken" is largely discoverable), which project
the idea belongs to, which initiative it might serve, and the vocabulary the
workspace already uses. Bring it into the questions as stated context, never as
a question.

**Guard against a duplicate.** The same search surfaces any PRD already
covering this ground. Where one exists, say so before interviewing and let the
user choose: extend the existing PRD (a re-install with `--replace`, below) or
write a genuinely distinct one under a different slug. Never silently author a
second PRD over the same idea.

## Template selection — start at `standard`, announce every switch

The plugin ships one template per tier, and the tiers nest additively:

- **`basic`** — `## Problem`, `## Solution`, `## Success criteria`.
- **`standard`** — `basic`'s sections plus `## Users`, `## Requirements`,
  `## Non-goals`. **This is the default.**
- **`comprehensive`** — `standard`'s sections plus `## Risks`, `## Rollout`,
  `## Open questions`.

Read the active tier's file under
`${CLAUDE_PLUGIN_ROOT}/skills/prd/references/` — it is the authority on the
sections and their order, and its italic guidance lines tell you what each
section must actually contain. **State the tier and its reason in one visible
sentence** before the interview starts (e.g. "Taking `standard` — one project,
no regulatory weight").

Escalate or de-escalate on what investigation found, judged relative to *this
workspace*, and **announce it the moment it happens** rather than at the end:

- **Escalate to `comprehensive`** when the idea carries blast radius across
  several projects, regulatory or risk weight, a phased rollout, or several
  distinct user classes.
- **De-escalate to `basic`** for a small, self-contained idea whose users and
  scope are obvious.

A switch never restarts the interview. Because the tiers nest, everything
already answered still belongs to the new tier: escalating only adds sections
to cover, and de-escalating keeps the extra answers as sections beyond the
tier's list, which the linter explicitly allows.

## The interview — one section per round

Interrogate section by section against the active tier, in the template's
order, until every required section can be filled with the **user's own
substance**. Each round:

- **Covers one section.** Ask **2–4 focused questions** about it, then fold the
  answers in before opening the next round. Do not sprawl across the whole
  template in one round, and do not drip a single question per turn.
- **Is grounded in investigation.** Open with what you already know from the
  code, the specs, and the workspace — then ask only what that could not
  settle. Restating discovered facts as questions wastes the round.
- **Offers concrete options, recommended default first**, so the cheapest reply
  is accepting your recommendation and overriding it costs one word.
- **Presses on thin answers.** A section answered with an adjective is not
  answered: "faster" is not a success criterion, "power users" is not a user
  class. Ask again with the sharper question rather than writing the vague
  version down.
- **Never invents filler.** A section with no substance behind it is a reason
  to keep asking, not to author plausible prose. The user's material is the
  only material a PRD carries.

**The vehicle.** Where the harness offers question dialogs, put each round in a
single AskUserQuestion call. Otherwise end the turn as plain text with the
round's questions numbered, options lettered, default first, and wait for a
typed reply.

Stop interviewing the moment the active tier's every required section can be
written from what the user gave you — an interrogation with nothing left to
learn is just an interrogation.

## Compose and install

1. **Settle the slug in the first round.** Kebab-case, naming the product idea
   (`mobile-push`, not `prd-1`), and confirmed with the user alongside the
   opening section — it is the PRD's directory name and its `# ` title, and
   renaming later means re-installing.
2. **Fill the template.** Start from the active tier's file and replace, in
   place: the `# <prd-slug>` title placeholder with the slug, and **each italic
   guidance line wholesale** with the section's content — the guidance is
   instruction to you, never text that ships. Keep `Status: draft` and the
   `Template:` line naming the active tier. Add `Initiative: <slug>` **only**
   when the user names a parent initiative that actually resolves in the
   workspace (`workspace-show` lists them); it is the only other recognized
   header key, and an unresolvable value fails the lint.
3. **Author into a staging file** — a `mktemp` path is fine. Never the
   workspace path, which the engine owns.
4. **Install through the engine**, which resolves the store path, validates the
   header and the tier's required sections, and on any finding restores what it
   replaced and exits non-zero:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py" \
       prd <slug> --from <staging-file>
   ```

   If it reports a finding, fix the staged file and re-run — nothing was
   installed. **Never finish on a non-zero emit**, and never write the PRD's
   workspace path by hand. Re-installing over an existing PRD requires
   `--replace`.
5. **Read it back through the engine** as the confirmation that it landed:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat prd <slug>
   ```

   This lands in the workspace, outside the repository, so the repo's
   worktree-and-PR workflow does not apply — there is no branch and no PR.

## Ending — hand off, don't decompose

When the PRD is installed and reads back clean:

1. **Summarize it** — the slug and where the engine installed it, the active
   tier and why it was chosen, and a line per section covering what the
   interview settled. Name any tier switch that happened along the way.
2. **State how approval works.** Emission wrote `Status: draft`. A PRD becomes
   approved by being **re-installed** with `Status: approved` in its header,
   through the same staged verb with `--replace` — there is no status CLI verb
   for a PRD, and the header is never edited in the store by hand.
3. **Point at `/s:epic`, on its own line** — a colon-terminated sentence, a
   blank line, then the command alone, so the one actionable string is easy to
   spot and copy:

   ```
   Decompose this PRD into an epic with:

   /s:epic
   ```

   An epic born from this PRD carries `PRD: <slug>` in its metadata, which the
   epic linter resolves through the workspace chain.
4. **Stop.** This skill never invokes `/s:epic` itself, never plans or builds a
   member change, and never writes a PRD's status by hand.

## Question rejection recovery

**Question rejection recovery.** A known Claude Code bug can deliver an
AskUserQuestion interaction as a tool rejection ("The user doesn't want to
proceed with this tool use") even when the user tried to answer. Never treat a
rejected or interrupted AskUserQuestion as a decline, a stop, or an answer.
When the user's next message arrives: if it answers the pending question, fold
it in and continue; otherwise re-offer the same choices as a plain-text
numbered list and wait for a typed reply. Only an explicitly selected or typed
stop/decline ends the flow.
