---
name: teach
description: >-
  Teach mikk: distill the repo's spec artifacts and answered queue entries into
  the workspace wiki. Scan the engine-mediated spec surfaces, interview the user
  only on the gaps and contradictions the scan surfaces, drain answered queue
  entries into pages, and ingest through the store's staged, lint-gated emit
  verb. Use when asked to "teach mikk", "distill knowledge into the wiki",
  "fill the wiki", "drain the queue", or "/s:teach". Trigger phrases: "teach
  mikk", "distill knowledge into the wiki", "drain the queue", "/s:teach".
---

# /s:teach — spec artifacts → workspace wiki pages

You are the **write path for the workspace wiki**. Your job is to distill the
invoking repo's durable spec artifacts (and any answered queue entries) into
wiki pages, interviewing the user only about the gaps and contradictions your
scan surfaces, and to install everything through the store's staged, lint-gated
emit verb. You are the counterpart to the `shipd:ask` oracle's read path: the
oracle answers from the wiki, and you are what fills it — `/s:ask` already
points users here as "the future teach-mikk write path" that drains answered
queue entries into pages.

**You never write into the store by editing its files in place.** Every store
mutation goes through one `spec_emit.py wiki --from <staging>` call over a
throwaway staging directory, so an interrupted or invalid run never corrupts the
store — the emit backs up the affected files, installs the staged subset, runs
the whole-store wiki lint, and restores byte-for-byte on any finding.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `shipd:teach
v<version>` in your first user-visible status sentence (e.g. "shipd:teach v0.6.8 —
scanning the repo's spec surfaces and distilling into the wiki"), so the user
can always see which plugin snapshot the session is running.

Throughout, the engine scripts are:

- **STATUS_CLI** — `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (all reads and the queue write).
- **EMIT_CLI** — `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py`
  (the one store write path).

Run every engine verb with `python3 <CLI> --root <repo-root> <verb …>`, where
`<repo-root>` is the invoking repo.

An **optional invocation argument** narrows the run to one topic or surface
(e.g. a capability name, an epic slug, or a subject keyword). When present,
scope the scan and the distillation to it; when absent, run the full bounded
sweep below. The one exception is the ledger-entry reference below — an
argument of the form `<change> Q<n>` — which runs a different flow entirely.
**Every other argument is handled exactly as before.**

## 0. Ledger-entry reference mode — `/s:teach <change> Q<n>`

**When the invocation argument matches `<change> Q<n>`** (a change slug followed
by a `Q` and a number, e.g. `/s:teach dark-mode-toggle Q1`), **bypass the
distillation sweep**: steps 2–5 do not run. The user is pointing at one recorded
ask-mikk consultation in that change's plan ledger (the plan's
`## Questions and answers` section) to correct the standing answer it captured.

1. **Resolve the store** exactly as in step 1 below — the correction still
   installs through the store's one staged write path.
2. **Resolve the change through the engine read**, which covers both a live
   change and one already archived:

   ```
   python3 STATUS_CLI --root <repo-root> cat change <change>
   ```

   `cat change` resolves `planned/<change>/` first and falls back to the newest
   archived `completed/*-<change>/`, so a merged change's ledger stays
   readable. If the read fails, or its `plan.md` carries no
   `### Q<n>:` entry of the referenced number, **report that and stop without
   writing anything** — no staging dir, no emit, no queue write.
3. **Print the entry in full** as user-visible text — its `### Q<n>:` header and
   every field (`**Question:**`, `**Verdict:**`, `**Answered by:**`,
   `**Answer:**`, and the `**Cited:**` or `**Queued:**` field it carries) — so
   the user sees exactly what was asked and what was answered before correcting
   it.
4. **Interview for the corrected standing position** in the plugin's house
   question shape: one plain-text round asking what the standing answer should
   be instead, and what the correction rests on. Keep it to that one round.
5. **Install the correction through the step 6 staged emit**, with three rules
   specific to this mode:
   - **Update the cited page, don't duplicate it.** When the entry carries a
     `**Cited:**` field naming a wiki page that exists, stage an updated version
     of *that* page carrying the corrected position — never a near-duplicate new
     slug. Only when the entry cites no existing page does the correction author
     a new page (with its `index.md` entry).
   - **Preserve the correction verbatim.** The user's typed correction exists
     nowhere else, so stage it as a dated, add-only `sources/<dated-file>` like
     any other interview answer.
   - **Drain the entry's queue block in the same ingest.** When the entry
     carries a `**Queued:** q-<slug>` and `cat wiki queue` still shows that
     block, remove it from the staged `queue.md` (per step 5's draining rules)
     so the queued question does not stay pending forever. A block that is
     already gone is not an error.

   The run's `log.md` entry names the change and the `Q<n>` it corrected.

Then report what was touched, as usual. Anything that does **not** match
`<change> Q<n>` falls through to the sweep below untouched.

## 1. Resolve the store

Resolve the workspace wiki store and its health first:

```
python3 STATUS_CLI --root <repo-root> wiki-show
```

`wiki-show` resolves the workspace (the nearest ancestor declaring a
`workspace` key) and prints the store's root, page count, coverage, last log
entry, and a `base:` line reporting whether a durable base store is layered
beneath this one (`base: <path> (present)`, `(absent)`, or `base: none`) — the
scan and the promotion routing below consume that line. Branch on the outcome:

- **No workspace discoverable** — `wiki-show` fails naming the missing
  workspace. Unlike the non-blocking oracle, `/s:teach` is user-invoked and
  interactive, so **stop**: name the missing workspace and point the user at
  `workspace-init` (`python3 STATUS_CLI --root <dir> workspace-init <path>`).
  Do **not** invent a store location or write anything.
- **Workspace but no store** — scaffold it once with
  `python3 STATUS_CLI --root <repo-root> wiki-init`. The verb refuses an
  existing store, so this call is safe to make only when `wiki-show` reported no
  store. After scaffolding, the store holds an empty `index.md`, `queue.md`,
  `log.md`, seeded `schema.md`, and empty `wiki/` and `sources/` directories.
- **Store present** — proceed to the scan.

## 2. Scan the repo's spec surfaces (engine reads only)

Scan the invoking repo's durable surfaces through **engine reads only** — never
raw file reads of `.shipd/` internals. Prefer decision-dense surfaces first:

1. `cat epic <slug>` — an epic's `## Decisions` / `## Design` (the densest
   source of standing positions).
2. `cat verified <capability>` — the verified capability masters' norms and
   contracts.
3. `cat research <slug>` — a linked research report's findings.
4. `project-show <slug>` — the project's declared context and repos.
5. Completed changes' plan decisions — `cat change <slug>` for changes the
   engine reports as completed, reading their `plan.md` `## Implementation`
   decisions.

**Prefer a declared focus project's surfaces first.** Read
`python3 STATUS_CLI --root <repo-root> workspace-show`; when it prints a
`focus:` line, scan that focus project's surfaces (via `project-show
<focus-slug>` and the artifacts it names) ahead of the others.

Then read the **existing wiki** so distillation updates pages instead of
duplicating them:

- `cat wiki index` — the page catalogue; note which pages already cover the
  surfaces you scanned.
- `cat wiki <slug>` — read each candidate page the index names as relevant.

**Read the base store's index too, when one is layered.** `wiki-show`'s `base:`
line (step 1) reports whether a durable base store sits beneath the job store.
When it reads `base: <path> (present)`, read the base store's index and its
candidate pages through the **same engine reads rooted at the base store
path** — `python3 STATUS_CLI --root <base-store-path> cat wiki index`, then
`cat wiki <slug>` for the pages that bear on your surfaces (and read-only grep
under that base store dir). **Treat a subject the base already covers as
covered:** do not stage a job-store page that duplicates a base page — a
base-worthy update routes through promotion (step 3) instead. Skip this base
read entirely on `base: none` or `(absent)`.

You may **widen** beyond the index with read-only `grep` under the store
directory `wiki-show` printed (matching page bodies for a subject's terms).
Never write through grep or edit any wiki file. (Retrieval is index- and
grep-based over markdown — no embeddings, no search service.)

## 3. Distill into pages

Distill the scanned surfaces into **entity/convention pages** that follow the
store's `schema.md` grammar (`cat wiki schema` for the seeded conventions):
kebab-case `wiki/<slug>.md` pages, `[[slug]]` wikilinks resolving to existing
pages, and a matching `index.md` entry per page.

- **Cite backing artifacts by name.** Every distilled page names the repo
  artifact behind its position — e.g. `epic/mikk-knowledge`,
  `verified/shipd-wiki`, `research/<slug>` — so a reader can verify the position
  against its source. Repo artifacts are **never copied into `sources/`**: the
  repos already hold them durably, and add-only sources would refuse a refresh.
- **Update, don't duplicate.** When an existing page already covers a surface,
  author an updated version of that page rather than a near-duplicate new slug.
- **Bound the run to 5–15 page touch-ups.** A single run touches at most 15
  pages, preferring the decision-dense surfaces first; the run's `log.md` entry
  records what was covered so a later run continues where this one stopped.
- **Honor the focus argument.** When the invocation named a topic or surface,
  scope the distillation to it.

### Classify job-scoped vs. job-independent (only when a base is present)

When `wiki-show` reported `base: <path> (present)`, classify each distilled
page **and each drained queue answer** as either:

- **job-scoped** (the default) — knowledge specific to this workspace/job; it
  lands in the job store; or
- **job-independent** — durable knowledge that would serve every job (a
  convention, a naming rule, a standing engineering position not tied to this
  repo). Job-independent items are the promotion candidates offered in the
  interview round (step 4) and, when accepted, install into the **base** store
  (step 6) rather than the job store.

When **no base is declared or the declared base is absent** (`base: none` or
`(absent)`), skip classification entirely: everything is job-scoped, lands in
the job store, and **no promotion is offered**.

## 4. Interview — gaps, contradictions, and promotion offers only

Interview the user **only** about gaps and contradictions your scan surfaces —
plus the promote-to-base offers your classification produced — never an
open-ended interview. A gap is a decision the surfaces reference but leave
unstated; a contradiction is two surfaces (or a surface and an existing page)
that assert incompatible positions; a promotion offer asks whether a
job-independent item (step 3) should land in the base store instead of the job
store.

- **If the scan surfaces no gaps, no contradictions, and no promotion offers,
  run no interview** — ingest the distilled pages without asking the user
  anything.
- Otherwise run **one batched round** in the plugin's house question shape:
  a visible **context brief** first, then **plain-text numbered options-first
  questions** with the recommendation listed first, answered by typed reply.
  **Promotion offers join this same single round** — one options-first question
  per job-independent item (recommend promotion; the alternative is keep it in
  the job store). A round opens for promotion offers **even when the scan
  surfaced no gaps or contradictions**.
- **Deferred items are queued, not lost.** Where the user defers a question,
  queue it via the engine in the compact-question shape (decision, options,
  recommendation):

  ```
  python3 STATUS_CLI --root <repo-root> wiki-queue-add <slug> \
    --question "<decision>" \
    --options "<the options>" \
    --recommendation "<the lean>" \
    --origin "teach"
  ```

  The queued block lands with `Answer: pending` so it compounds into a later
  run instead of vanishing. (Do this queue write directly through the verb; it
  is separate from the staged ingest below.)

## 5. Queue draining

Drain **answered** queue entries in the same ingest. Read the queue with
`cat wiki queue`, then for **every `## q-<slug>` block whose `Answer:` line is
not `pending`**:

- distill its supplied answer into wiki page content, and
- **remove that block** from the staged `queue.md`.

Blocks whose `Answer:` is `pending` are left **untouched** — the queue stays a
pending-only worklist. The run's `log.md` entry names each drained `q-<slug>`.

## 6. Ingest — the one staged write path

Author the touched store subset in a throwaway staging directory and install it
with a single emit call. Never edit store files in place.

1. Create a staging dir: `staging=$(mktemp -d)`.
2. Write the **touched subset** into it, mirroring the store layout:
   - `wiki/<slug>.md` — each new or updated page.
   - `index.md` — the **full** index catalogue, with `- [[slug]] — <summary>`
     entries kept in step with the touched pages (the entry set and the store's
     page set must match exactly after install, so include existing entries too,
     read from `cat wiki index`).
   - `queue.md` — the **full** queue with the drained (answered) blocks removed
     and every pending block preserved, when the run drained anything.
   - `log.md` — the **full** log with a new dated entry appended describing the
     run (`## [YYYY-MM-DD] teach | <subject>`), naming the covered surfaces and
     any drained `q-<slug>`s.
   - `sources/<dated-file>` — interview and drained-queue answers preserved
     **verbatim** as a dated, add-only file (these answers exist nowhere else).
     Sources are immutable, so use a fresh dated filename; never restage an
     existing source path. Do **not** copy repo artifacts here.
3. Install the whole staged subset with one call:

   ```
   python3 EMIT_CLI --root <repo-root> wiki --from "$staging"
   ```

   The emit recognizes only `index.md`, `log.md`, `queue.md`, `wiki/<slug>.md`,
   and `sources/<file>`; it backs up the affected files, installs the staged
   set, runs the whole-store wiki lint, and — on any finding — restores every
   affected file byte-for-byte and exits non-zero, so an invalid store state
   never lands. If it fails validation, read the findings, fix the staged files,
   and re-run; nothing was installed.

**Wikilinks stay store-local.** No staged page — in either the job or the base
staging dir — may `[[link]]` a page that lives only in the *other* store. The
wiki lint resolves `[[slug]]` links within one store, so a cross-store link
would fail that store's lint (and make validity machine-dependent). Author each
page to link only pages that live in the store it installs into.

### 6a. Promotion — a second staged write, rooted at the base store

When the user accepted any promotion offers (step 4), install the promoted
job-independent items into the **base** store through a **second, separate**
staged emit rooted at the base store path:

1. Build a **second** staging dir holding only the promoted subset:
   `wiki/<slug>.md` for each promoted page, plus the base store's **own full
   `index.md`** (read it with `python3 STATUS_CLI --root <base-store-path> cat
   wiki index`, keep every existing entry, add one per promoted page) and the
   base store's own
   `log.md` with a fresh dated `## [YYYY-MM-DD] teach | <subject>` entry
   naming the promoted slugs. Preserve any interview/answer text behind a
   promoted page as a dated `sources/<file>` in this base staging dir.
2. Install it against the base store:

   ```
   python3 EMIT_CLI --root <base-store-path> wiki --from "$base_staging"
   ```

   Rooting the emit at the base store path makes it operate on (and lint, and
   auto-commit in the base workspace repo) the base store, not the job store.
3. **Promoted items land in the base store only** — they do **not** also appear
   in the job store's staging from step 6. Promotion never removes an existing
   job-store page; it only adds to the base.

When no promotion was accepted (or no base is present), skip 6a entirely.

**Every ingest keeps each touched store's `index.md` in step with its pages and
appends a dated `log.md` entry.** Then report to the user: the pages touched in
the job store, any pages promoted to the base store, any `q-<slug>`s drained,
any items queued for a person, and the store(s) the run wrote to.
