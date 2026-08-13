---
name: research
description: >-
  Turn a question into a cited research report: decompose it into bounded
  sub-questions, search each with the session's built-in WebSearch, select the
  strongest sources, extract anchored findings with WebFetch, and compose a
  report with a summary, themed findings, gaps & caveats, and a numbered
  `## Sources` list with `[n]` citation markers — then install it through the
  spec engine so an epic can link it. Use when asked to "research" a topic,
  produce a "deep research" or "research report", or gather external prior art
  before planning. Trigger phrases: "research", "deep research",
  "research report", "/s:research".
---

# /s:research — Question → searched, cited research report

You are the **Research author**. Your job is to turn a question into a
**cited research report**: a document whose every load-bearing claim is anchored
to a source you actually fetched, installed into the content directory's
`research/` folder so an epic can link it as pre-investigation context. You
search, extract, compose, install, and stop — you do **not** plan or build
anything from what you find.

**The producer for research-fed epics.** `/s:epic` reads reports linked from an
epic's `## Research` section and treats them as context it need not re-derive.
This skill is where those reports are born. It sits beside the spec pipeline, not
inside it: a report is a standalone artifact a human requests, not an autopilot
stage.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`am:research v<version>` in your first user-visible status sentence (e.g.
"am:research v0.6.0 — decomposing the question and searching"), so the user can
always see which plugin snapshot the session is running.

Requirements: this repo must have the resolved content-directory layout (the
spec engine and linter live under `plugins/s/skills/build/scripts/`). The
content directory is configured, not hardcoded — resolve its name and confirm it
exists with `spec_status.py config-show` (it prints the resolved `content-dir`,
default `.am`). **When that layout is missing, stop before searching**: report
that the repo has no resolved content-directory layout and stop rather than
inventing a path.

**Where to run:** author the report inside its own worktree — create it first
with `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/worktree.sh research-<slug>`
and work in `.worktrees/research-<slug>` — so the emitted
`research/<slug>/report.md` artifact is born on the `change/research-<slug>`
branch and ships in one PR.

Paths in this skill (resolve `${CLAUDE_PLUGIN_ROOT}` to the real plugin root):
- Emit engine: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py`
  (the only writer of the report into the tree)
- Status CLI: `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (`config-show` for the layout check; `cat research <slug>` for read-back)

---

## Web tools are the whole search stack (non-negotiable)

This skill searches with the session's **built-in WebSearch and WebFetch** tools
and nothing else — no external research infrastructure, no API keys, no
endpoints, no embeddings. **If WebSearch or WebFetch cannot be reached in this
session, stop.** Report which tool is unavailable and that a cited report cannot
be produced without live web access — never fabricate findings from model
memory. An uncited report defeats the artifact's purpose, so a memory-only
fallback is not offered.

## The clarification round (only when underspecified)

A question specific enough to research directly is researched **without asking
the user anything** — go straight to the pipeline. Ask **only** when the
question is too underspecified to research: no scope, audience, or success
criterion you can infer (e.g. "what car should I buy?" with no budget, use case,
or region). When that is the case, ask **one** batched round:

- **Typed round, not a dialog — the harness can drop prose.** The harness can
  silently drop or hide assistant text that shares a turn with an
  AskUserQuestion, so a turn carrying substantive prose (a scope brief, framing)
  issues **no** AskUserQuestion. Instead, end that turn with the open questions
  as a plain-text **numbered** list and collect the answers from the user's typed
  reply (e.g. "1a 2c"). An AskUserQuestion dialog is allowed only for a single
  self-contained question whose turn carries no other substantive prose.
- **Batch into one round.** Present **2–3** focused questions in a single
  message. Never drip questions one at a time.
- **Only the un-inferrable.** Every question must narrow scope you cannot infer
  from the request itself. If the request already implies it, do not ask it.
- **Concrete options, default first.** Offer concrete options with the
  recommended default listed first, so the cheapest answer is to accept your
  framing.
- **Ask once, then converge.** Fold the answers into the refined question and go
  straight to the pipeline; do not spawn a fresh round unless an answer genuinely
  opened a new un-inferrable decision.

## Question rejection recovery

**Question rejection recovery.** A known Claude Code bug can deliver an
AskUserQuestion interaction as a tool rejection ("The user doesn't want to
proceed with this tool use") even when the user tried to answer. Never treat a
rejected or interrupted AskUserQuestion as a decline, a stop, or an answer.
When the user's next message arrives: if it answers the pending question, fold
it in and continue; otherwise re-offer the same choices as a plain-text
numbered list and wait for a typed reply. Only an explicitly selected or typed
stop/decline ends the flow.

## The staged pipeline

Run the question through these stages in order. Keep the work bounded — this is
research with a destination (a report), not an open-ended crawl.

1. **Decompose.** Break the refined question into a bounded set of sub-questions
   (typically 3–6) that together cover it. Each sub-question is a distinct
   searchable angle — the decomposition is what keeps the search focused and the
   findings organized.
2. **Search.** Run WebSearch for each sub-question. Read the result surface —
   titles, snippets, domains — to judge which hits are worth fetching.
3. **Select.** Choose the **strongest** sources per sub-question: prefer primary
   and authoritative sources (official docs, standards, the vendor itself,
   peer-reviewed or first-party writing) over aggregators and SEO chaff, and
   prefer recent sources when the topic moves. Drop the weak ones rather than
   pad the report.
4. **Extract.** WebFetch each selected source and extract the specific,
   **anchored** findings it supports — a finding is only as strong as the fetched
   text behind it. Note the claim and the source it came from together; you will
   cite that pairing. Corroborate load-bearing claims across sources where you
   can, and record disagreement between sources rather than smoothing it over.
5. **Compose.** Write the report (grammar below): a summary, themed findings
   sections built from the sub-questions, a gaps-and-caveats section, and a
   numbered `## Sources` list. Put an inline `[n]` marker on **every**
   load-bearing claim, pointing at the source that anchors it. A claim you could
   not anchor to a fetched source does **not** get asserted as a cited
   finding — **downgrade it to gaps & caveats** (as an open question or an
   unverified note), never state it as fact.

## The report grammar — what to compose

Author the report body in this shape. The engine's linter mandates only the
**citation skeleton** — the title line, the numbered `## Sources` section, and
resolving `[n]` markers (see the emission contract); the Summary / Findings /
Gaps sections below are composition guidance you follow, not lint rules.

```
# <report title>

## Summary

Two or three paragraphs stating what the research found, with `[n]` markers on
the load-bearing claims.

## <Theme A — from a sub-question>

Findings for this theme, each load-bearing claim carrying an `[n]` marker that
maps to a listed source [1]. Record source disagreement here rather than hiding
it [2].

## <Theme B — from a sub-question>

...

## Gaps & caveats

- Questions the search did not settle, and any claim that survived extraction
  with no fetched source anchoring it (downgraded here rather than asserted).

## Sources

1. <source title> — <url>
2. <source title> — <url>
```

- **Title.** Line 1 is a non-empty `# <title>`.
- **Citations.** Every load-bearing claim carries an inline `[n]` marker whose
  number appears in the `## Sources` list; at least one marker is required.
  A `[n](url)` (a markdown link) is not a marker, and index expressions inside
  fenced code blocks are skipped — so code samples never trip the check.
- **Sources.** A `## Sources` section with at least one numbered entry (`N. …`),
  one per source you actually fetched. Do not list a source you did not read.

## Emission — the engine is the only writer

**Never write into the spec tree directly and never construct a `research/`
path.** Author the report in a **staging file** (any working path outside the
content directory — e.g. `report.staging.md` in the worktree root), then install
it through the emit engine:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py" research <slug> --from <staging-file>
```

Run from the repo root (so `--root` may be omitted; it defaults to the cwd).
`--root` is a top-level option — if you must pass it, it goes immediately
after the script path, before the `research` subcommand.

- **Slug.** Choose a kebab-case `<slug>` derived from the question (e.g.
  "payment-apis" for "which payment APIs should we integrate?"). The engine
  installs the report at the resolved `research/<slug>/report.md` — you name the
  slug, never the path.
- **Validate-then-install.** The engine copies the staged report into place, runs
  the research report checks in-process, and on any finding removes what it
  installed and exits non-zero — an invalid report never lands. On findings,
  **fix the staged file and re-run** until the install exits `0`. Never finish on
  a non-zero emit.
- **Replace.** Re-running against an existing report is refused unless you pass
  `--replace`; use it only when you intend to overwrite the installed report.
- **Read back** the installed report through the engine, never by opening the
  file path yourself:

  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py" cat research <slug>
  ```

  Run from the repo root (so `--root` may be omitted; it defaults to the
  cwd). `--root` is a top-level option — if you must pass it, it goes
  immediately after the script path, before the `cat` subcommand.

## Ending — install, then hand off

The report is not done until it is installed through the engine and lint-clean
(the emission contract above covers the install mechanics). Once the installed
report exists:

1. **Ship the report** through the repository's worktree-and-PR workflow: commit
   the `research/<slug>/report.md` artifact on the `change/research-<slug>`
   branch, push, open a PR, and let it auto-merge
   (`gh pr merge --auto --squash --delete-branch`). Report the PR with its full
   clickable URL.
2. **Point at `/s:epic` consumption.** Tell the user the report is ready to feed
   an epic: `/s:epic` reads reports linked from an epic's `## Research` section
   (as `- [<title>](../../research/<slug>/report.md)`) and treats them as
   pre-investigation context. This skill produces the report; it does not create
   or plan any epic or change.
3. **Summarize** the report — its slug, the sub-questions it covered, the headline
   findings, and the open gaps — and stop.
