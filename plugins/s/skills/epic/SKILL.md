---
name: epic
description: >-
  Decompose a feature into an epic: investigate the codebase first, ask the user
  only what can't be inferred (one batched round), record the epic's Decisions
  and Design, and emit the stub table of member changes with complexity ratings
  — then stop. Member changes are planned later, one at a time, via /s:plan.
  Invoked as `/s:epic <slug> amend`, runs the amendment flow on a live epic
  instead: stamped Decisions and shelf edits only, gated by the linter and
  `epic-amend-check`, then shipped as a PR from a fresh `epic-amend-<slug>`
  worktree — or, where the epic resolves into an external store, as one scoped
  local commit in the store's repository. Use
  when asked to "create an epic", "decompose a feature", "group changes", "amend
  an epic", or plan a multi-change initiative before spec'ing the individual
  changes. Trigger phrases: "epic", "create an epic", "decompose", "amend the
  epic", "/s:epic".
---

# /s:epic — Convergent epic authoring → stub-table emission

You are the **Epic author**. Your job is to turn a feature too large for a single
change into an **epic**: a decomposition into member changes, captured as a stub
table, with the shared Decisions and Design recorded once so each member change
inherits them. You converge, emit the epic, and stop — you do **not** plan or
build the member changes.

**The grouping layer.** An epic sits above changes in the
Initiative → Epic → Change hierarchy. It owns the cross-cutting decisions and the
list of member changes; each member is born later in its own worktree via
`/s:plan`, carrying an `Epic: <slug>` line back to this epic.

Requirements: this repo must have the resolved content-directory layout (the
spec engine and linter live under `plugins/s/skills/build/scripts/`). The
content directory is configured, not hardcoded — resolve its name and confirm it
exists with `spec_status.py config-show` (it prints the resolved `content-dir`,
default `.shipd`).

Path notation: literal `.shipd/` paths in this skill denote the repo's resolved
content directory (default `.shipd`) — resolve the actual name with
`spec_status.py config-show` (its `content-dir:` line) and substitute it when
the repo configures another.

**Where to run:** author the epic inside its own worktree — create it first with
`"${CLAUDE_PLUGIN_ROOT}/bin/shipd" worktree epic-<slug>` and work in
`.worktrees/epic-<slug>` — so the
emitted `.shipd/epics/<slug>/` artifact is born on the `change/epic-<slug>` branch and
ships in one PR.

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):
- Spec linter: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_lint.py`
  (a sibling skill in the same plugin — this cross-reference is intended)
- Status CLI: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (drives the epic's lifecycle status; used to promote to `ready` at approval)

---

## Amend mode (live-epic amendment)

**When the invocation is `<slug> amend`, run this mode instead of the authoring
flow — before investigating, before any question round, before anything.** The
epic already exists; nothing below the Codebase-first rule runs, and no epic is
emitted through staging.

A live epic accretes but does not drift. Only the **amendable** regions may
change: the `## Decisions` section and the shelf sections `## References`, plus
a pre-existing `## Research` or `## Video` extended in place. `## Introduction`,
`## Design`, the `## Changes` stub table, and the header metadata are
**protected** — an amendment that needs one of those is a re-decomposition, not
an amendment; say so and stop.

1. **Resolve the epic and refuse a draft.** Read it through the engine:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" --root <repo-root> cat epic <slug>
   ```

   A slug that resolves to no epic → report that and stop. An epic at
   `Status: draft` → **refuse the amendment**: a draft is still being authored,
   so it is edited in its own `epic-<slug>` authoring worktree, not amended.
   Say that and stop.

   **Then detect the store case**, because it decides which of the two
   shipping paths the rest of the flow takes:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" --root <repo-root> config-show
   ```

   A `store:` line prints exactly when the configuration declares
   `store_root` — the content directory, and with it the epic, lives in an
   **external store** that is a different git repository from the consuming
   repo. That is the **store path**, flagged inside steps 2, 5 and 6 below;
   the `store:` line's value is the store's content directory, so the epic
   sits at `<store content dir>/epics/<slug>/epic.md`. With no `store:` line
   the steps run exactly as written.

2. **Work in a fresh worktree** — the in-repo case, where the epic is tracked
   in the consuming repository. Create it and make every edit inside it, so the
   amendment is born on `change/epic-amend-<slug>` and ships in one PR:

   ```
   "${CLAUDE_PLUGIN_ROOT}/bin/shipd" worktree epic-amend-<slug> --fresh
   ```

   `--fresh` is not optional: it guarantees the worktree is cut from the root
   checkout's HEAD rather than adopting a stale amendment branch.

   **Store path:** skip this step entirely. Under a store there is no
   amendment worktree, no `change/epic-amend-<slug>` branch, and no pull
   request in *either* repository — the consuming repo is not the one holding
   the epic, and the store's working tree is shared by every repo pointed at
   it, so it is never flipped onto a branch. Make the steps 3 and 4 edits
   directly in the store's working tree, exactly as written, and leave them
   **uncommitted** — the gates in step 5 run against that uncommitted edit.

3. **Classify the amendment's substance** against the capture rubric
   (`references/capture-rubric.md`) before writing anything, and route it:
   - **Binding on every member** → one new (or extended) `## Decisions` bullet.
   - **Reference** → install it through the emit engine
     (`spec_emit.py docs <slug> --from <file>`) and link it from
     `## References`. **Never paste a document's content into `## Decisions`.**
   - **Durable** → it outlives the epic: hand it to `/s:teach` for the wiki, and
     amend nothing here.
   - **Noise** → dropped, deliberately.

   An item that is not epic-scope binding does not belong in this epic's
   Decisions, however true it is.

4. **Stamp every Decision you touch.** Each new or extended Decision bullet
   carries a dated provenance marker:

   ```
   *(amended YYYY-MM-DD: <one-line note>)*
   ```

   using today's real date. **Existing Decision text is never rewritten or
   deleted** — a superseded decision is recorded as a stamped addition beneath
   the original, so the epic keeps its own history.

5. **Pass both gates before shipping.** The linter, then the amendment gate:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_lint.py" --epic <slug> --root <repo-root>
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" --root <repo-root> epic-amend-check <slug>
   ```

   `epic-amend-check` compares the worktree's epic against its content at the
   merge-base of `HEAD` and `main` (override with `--base <ref>`) and exits `4`
   printing one `protected-section <name>` line per changed protected region
   (`header` for the title-and-metadata block). **A finding stops the flow:**
   revert that region to its base content and re-run — never push past it. A
   non-zero exit that is not `4` is an error (no epic at the base, an
   unresolvable ref, no git work tree); report it and stop.

   **Store path:** both commands are unchanged, and `--root` still names the
   **consuming repository**, never the store — the engine resolves the store
   from that repo's configuration, and `epic-amend-check` anchors its git
   lookups on the directory holding the epic, so the base is read from the
   store's own history. Because the store edit is still uncommitted, the gates
   compare it against the store's last committed state, which is exactly the
   accretion check. Run them **before** the step 6 commit: a store that is not
   inside any git work tree has no base to read, so `epic-amend-check` errors
   naming the epic's directory — a non-zero exit that is not `4`, which stops
   the flow under the rule above with nothing committed.

6. **Ship it as a PR — in the in-repo case**, per the repository's workflow:
   commit the epic edit on `change/epic-amend-<slug>`, push, `gh pr create`,
   post the semantic-review gate, and let it auto-merge. Report the PR with its
   **full clickable URL**. Never edit a live epic on `main` and never push
   directly.

   **Store path — one scoped local commit instead.** There is no PR to open.
   Once both gates pass, commit the epic file **alone** in the store's own
   repository, mirroring the engine's local-commit-never-push discipline for
   writes into an external store:

   ```
   git -C <store repo root> add <store content dir>/epics/<slug>/epic.md
   git -C <store repo root> commit -m "shipd: amend epic <slug>"
   git -C <store repo root> rev-parse --short HEAD
   ```

   Stage that one path only — never `add -A`, never `commit -a` — so an
   unrelated edit sitting in the shared store's working tree is not swept in.
   **Never push**, and never create a branch there. Report the commit hash in
   place of a PR URL.

7. **Summarize and stop** — what was amended, its tier, and how it shipped: the
   PR URL in the in-repo case, the store commit's hash on the store path. Amend
   mode plans no member change and re-decomposes nothing.

## Codebase-first rule (non-negotiable)

**Investigate before you ask.** Before putting a single question to the user,
read the repository: existing capabilities under `.shipd/verified/`, in-flight
changes under `.shipd/planned/`, existing epics under `.shipd/epics/`, the relevant code,
and the user's request itself. **Never ask the user anything whose answer is
discoverable from the repo or the request** — the affected modules, existing
patterns, current behavior, and naming conventions are yours to find, not to ask
about. A question you could have answered by reading is a failure of this skill.

## Flow

1. **Investigate.** Read the request and the codebase until you understand the
   feature's scope, the capabilities it touches, and the natural seams along
   which it decomposes into member changes. **Read any supplied research first:**
   when the user names research reports, or points authoring at files under the
   content dir's `research/` folder, read those reports as pre-investigation
   context before your question round — they may already answer questions you
   would otherwise ask. Record every report you actually read as a link entry in
   the epic's `## References` section (see the epic contract) — new authoring
   prefers `## References`, though a pre-existing `## Research` section may be
   extended in place instead — and never invent an entry for a file you did not
   read. **Install a supplied document that does not already live under
   `research/`, `video/`, or `docs/`:** when the user points authoring at a
   context document elsewhere — a strategy doc, a verbatim brief the members
   must build from — install it through the emit engine first, so the epic can
   link it and every downstream skill can read it back:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py" docs <slug> --from <file>
   ```

   (`--root` precedes the subcommand when the working directory is not the
   repo root — `spec_emit.py --root <repo-root> docs <slug> --from <file>` —
   trailing it after the subcommand is rejected.) Pick `<slug>` as the
   kebab-case form of the document's level-1 title, or of its filename when the
   document carries no title. Where the first line is not a level-1 title,
   stage a **copy** that prepends a `# <title>` derived from the filename and
   install that copy — the user's original file is never edited. Then read and
   link the installed document as a `## References` entry. The engine
   validates the title but demands no citation skeleton, so an uncited
   document installs clean. **Never copy a document into the spec tree
   yourself** — a raw write into `docs/` is forbidden, the emit engine is the
   only writer. A file the user names that is already under the content dir's
   `research/`, `video/`, or `docs/` folder is read and linked as before;
   nothing is reinstalled. **Read any supplied video brief the same
   way:** when the user names a video bundle slug, or points authoring at a
   brief under the content dir's `video/` folder, read it with
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat
   video <slug>` as pre-investigation context before your question round.
   Record every brief you actually read as a link entry in the epic's
   `## References` section (see the epic contract) — a pre-existing `## Video`
   section may be extended in place instead — and never invent an entry for a
   brief you did not read. **The brief is an input to investigation, never a
   replacement for it:** the codebase-first rule above still applies in full —
   the affected capabilities and the decomposition seams are still established
   by reading the repository, not taken from the brief alone. **This skill does
   not ingest recordings:** when the invocation argument names a video
   container rather than an installed brief, report that and point the user at
   `/s:video-ingest` to produce the brief first — `/s:epic` consumes only
   briefs already installed under the content dir's `video/` folder.
2. **Ask only what remains** — and only if something remains. If genuinely
   un-inferrable decisions are left (the decomposition boundaries, a shared
   architectural choice, the theme/initiative), batch them into a **single**
   AskUserQuestion call (see the question contract below). If investigation
   already settled everything, ask nothing and go straight to emission.
3. **Emit** the epic at `.shipd/epics/<slug>/epic.md` (see the epic contract below),
   at `Status: draft`. Draft the `## Introduction` first — the why-first
   narrative and its `### Non-goals` — before the Decisions, Design, and Changes
   sections, so the epic opens with what the feature is and why it exists.
4. **Self-review** before the lint gate: re-read the drafted epic for
   placeholders, a decomposition that does not cover the feature, stub rows whose
   ratings are unconsidered, and Decisions/Design that leave a member author
   guessing. Fix what you find before linting.
5. **Lint** the emitted epic and fix findings until it is clean (see the lint
   gate below).

The moment the decomposition is settled and recorded, stop investigating and
emit — do not open new threads of exploration.

## The question contract (AskUserQuestion)

When decisions remain that you truly cannot infer, ask them under this
discipline — it is what separates a lean gate from an interrogation:

- **Batch into one call.** Issue a *single* AskUserQuestion containing **2–4**
  focused questions. Never drip questions one at a time.
- **Only the un-inferrable.** Every question must be a decision the codebase and
  the request cannot answer. If you could find it by reading, read it.
- **Concrete options, default first.** Each question offers concrete options, the
  **recommended default listed first**, so the cheapest answer is to accept your
  recommendation.
- **Ask once, then converge.** After the answers come back, fold them in and
  proceed to emission — do not spawn a fresh round unless an answer genuinely
  opened a new un-inferrable decision.
- **Classify what each answer carries.** An answer rarely carries only the
  decision you asked about. Before folding one in, classify its substance
  against the knowledge capture rubric
  (`${CLAUDE_PLUGIN_ROOT}/skills/epic/references/capture-rubric.md`) into
  **exactly one** of its four tiers, and act on that tier:
  - **Binding** — a constraint every member change must obey. It lands in the
    `## Decisions` section you are authoring. The epic does not exist yet, so
    there is nothing to amend: write the Decision directly.
  - **Reference** — material a member author consults rather than obeys. It
    installs through the emit engine (`spec_emit.py docs <slug> --from <file>`,
    step 1 above) and is linked from `## References`; its substance is not
    copied into `## Decisions`.
  - **Durable** — a standing position, convention, or workspace fact that
    outlives this feature. It routes to the workspace wiki via `/s:teach` or
    the oracle queue, not into the epic; the epic records only what its members
    are bound by.
  - **Noise** — session logistics, vented frustration, a tangent that changed
    nothing. Dropped deliberately, recorded nowhere.

  The rubric's calibrated examples and tie-breakers settle borderline cases; a
  single answer may split across tiers, each part routed on its own.

## Question rejection recovery

**Question rejection recovery.** A known Claude Code bug can deliver an
AskUserQuestion interaction as a tool rejection ("The user doesn't want to
proceed with this tool use") even when the user tried to answer. Never treat a
rejected or interrupted AskUserQuestion as a decline, a stop, or an answer.
When the user's next message arrives: if it answers the pending question, fold
it in and continue; otherwise re-offer the same choices as a plain-text
numbered list and wait for a typed reply. Only an explicitly selected or typed
stop/decline ends the flow.

## The epic contract — what to emit

Write `.shipd/epics/<slug>/epic.md` where `<slug>` is a kebab-case name matching the
directory:

```
# <slug>
Status: draft
Theme: <kebab-theme>            (optional)
Initiative: <kebab-initiative>  (optional)

## Introduction

The why first — the problem and its motivation — then the what (the feature in
brief) and its intended outcome, with success criteria recommended. Close with
a `### Non-goals` subsection listing the scope exclusions. This mirrors
`plan.md`'s Idea grammar, so one editorial convention covers both artifacts.

### Non-goals

- <what this epic explicitly does not do>

## Research                        (optional)

- [<report title>](../../research/<name>/report.md) <optional annotation>

## Video                           (optional)

- [<brief title>](../../video/<slug>/brief.md) <optional annotation>

## References                      (optional)

- [<title>](../../docs/<slug>/doc.md) <optional annotation>

## Decisions

The cross-cutting decisions every member change inherits — the shared
architectural choices, constraints, and rejected alternatives.

## Design

The shape of the feature as a whole: the pieces, how they fit, the seams the
decomposition follows.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| <member-slug> | <one-line description> | low | medium | low | low |
```

Rules the linter enforces (so get them right up front):

- **Header.** `# <slug>` title matching the directory; `Status:` one of `draft`,
  `ready`, `active`, `complete` (there is **no** epic-level `verified`). The
  optional metadata block recognizes only `Theme:` and `Initiative:`
  (kebab-case); `Profile:` and `Epic:` are **not** valid on an epic. When
  `.shipd-config.json` declares a non-empty `valid_themes`, `Theme:` must be one of
  them.
- **Sections.** All four of `## Introduction`, `## Decisions`, `## Design`,
  `## Changes` are required, and `## Introduction` must be the **first** level-2
  section — the why-first narrative precedes any technical content. The
  Introduction must carry a `### Non-goals` subsection.
- **Research (optional).** `## Research` is optional — omit it entirely for a
  feature with no research. When present it must hold at least one markdown list
  entry `- [title](path)` whose link resolves (epic-dir-first, then repo-root)
  to an existing file under the content dir's `research/` folder; the
  epic-relative form (`../../research/<name>/report.md`) is the clickable
  convention. An empty `## Research` section, a dead link, or a link to a file
  outside `research/` is a lint error. List only reports you actually read —
  never invent entries.
- **Video (optional).** `## Video` is optional — omit it entirely for a feature
  with no video brief. When present it must hold at least one markdown list
  entry `- [title](path)` whose link resolves (epic-dir-first, then repo-root)
  to an existing file under the content dir's `video/` folder; the
  epic-relative form (`../../video/<slug>/brief.md`) is the clickable
  convention. An empty `## Video` section, a dead link, or a link to a file
  outside `video/` is a lint error. List only briefs you actually read — never
  invent entries.
- **References (optional).** `## References` is optional — a superset shelf
  linking reference documents of any installed kind (research reports, video
  briefs, and supplied docs) that mixes freely with `## Research` and
  `## Video`. When present it must hold at least one markdown list entry
  `- [title](path)` whose link resolves (epic-dir-first, then repo-root) to an
  existing file under the content dir's `research/`, `video/`, or `docs/`
  folder. An empty `## References` section, a dead link, or a link to a file
  outside all three folders is a lint error. List only documents you actually
  read — never invent entries. New authoring prefers `## References`, but
  `## Research` and `## Video` stay valid forever and are never migrated.
- **Stub table.** The header row must be exactly the six columns in order. At
  least one data row. Each `Change` cell is a kebab-case slug, unique within the
  table. Each of the four rating cells (Code, Integration, Unknowns, Risk) is one
  of `low`, `medium`, `high` — your honest per-change complexity estimate.

Slugs are repo-unique by convention: a member slug should not collide with an
unrelated existing or archived change of the same name.

## Lint gate — emission is not done until lint is clean

After authoring the epic, lint it and do not declare the epic complete until it
passes:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_lint.py" --epic <slug> --root <repo-root>
```

Run from the repo root (so `--root` may be omitted, defaulting to the cwd). If
the linter reports any error, **fix the epic and re-run** — repeat until it exits
`0` and prints `OK`. Never finish on a non-zero lint.

## Ending — hand off, don't plan the members

`s:epic` is standalone: it ends when the epic is emitted and lint-clean. When
that point is reached:

1. **Promote to `ready` on approval.** Emission wrote the epic at
   `Status: draft`. Reaching a lint-clean, approved epic advances the status via
   the guarded verb (which re-checks that the epic lints clean before writing):

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" epic-set-status ready <slug> --root <repo-root>
   ```

2. **Ship the epic** through the repository's worktree-and-PR workflow: commit
   the `.shipd/epics/<slug>/` artifact on the `change/epic-<slug>` branch, push, open
   a PR, and let it auto-merge (`gh pr merge --auto --squash --delete-branch`).
   Report the PR with its full clickable URL.
3. **Point at `/s:plan` per member — do not plan them here.** This skill
   **never** creates member changes: it adds no directories under `.shipd/planned/`.
   For each stub row, tell the user to run `/s:plan <member-slug>`, which is
   where that member change is born (in its own worktree) carrying
   `Epic: <slug>`.
4. **Summarize** the epic — its slug, the Decisions/Design captured, and the
   member stub rows with their complexity ratings.
5. **Stop.** Do **not** start planning or implementing any member change. Epic
   authoring is done; planning each member is a separate, user-initiated step.
