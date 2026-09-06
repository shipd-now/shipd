# Knowledge capture rubric — where arriving information belongs

Information arrives mid-flow constantly: a typed answer to a question round,
a document the user pastes, a mid-build interjection, an aside about how this
team does things. Each such item has exactly one home — the change's binding
artifacts, the feature's reference shelf, the durable wiki, or deliberately
nowhere. Classify every substantive item into exactly **one** of the four
tiers below, then act on that tier. The rubric classifies; the skill and the
user still decide.

**This is the knowledge capture rubric, not the capture durability rubric.**
The durability rubric (`plugins/s/skills/ask/references/capture-rubric.md`)
answers one narrower question — whether an oracle-queued answer becomes
standing wiki knowledge, and with what authority. This rubric routes *all*
arriving information across four destinations, and hands its durable tier
off to the durability rubric rather than restating it (tier 3).

## The four tiers

### 1. Binding — changes what executors do

Information an executor must **obey**: a constraint on the implementation, a
scope cut, a settled architectural choice, a rejected alternative that must
stay rejected. Its home is decided by **scope**.

- **Change scope** — it binds this change only. It lands in the change's own
  artifacts: `plan.md`'s `## Implementation` for a technical decision,
  `plan.md`'s `## Questions and answers` ledger for the resolution and who
  settled it, a delta spec when it changes the contract itself. In a build,
  the artifacts are updated **before** the answer goes back to the executor,
  so the spec stays the single source of truth.
- **Epic scope** — it binds every member change, so it belongs in the epic's
  `## Decisions`. A live epic's Decisions change **only** through the
  sanctioned amendment discipline, never a free edit of the epic file:
  a fresh worktree (`shipd worktree epic-amend-<slug> --fresh`), the amended
  Decision stamped with a dated provenance line, the epic re-linted, and the
  edit shipped as an auto-merging pull request — the same discipline an epic
  status derivation ships under. A skill that meets epic-scope binding
  information mid-flow surfaces it to the user for that amendment; it does
  not edit the epic in passing.
- **During epic authoring** the epic does not exist yet, so there is nothing
  to amend: binding information goes straight into the `## Decisions` section
  being written.

### 2. Reference — supports the feature without binding executors

Material an executor **consults** rather than obeys: a strategy memo, meeting
notes, an API excerpt, a competitive teardown, a verbatim brief. It informs
judgment; nothing breaks if a task never opens it.

Install it through the emit engine — never copy a document into the spec tree
by hand:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py" docs <slug> --from <file>
```

Research reports and video briefs keep their own kinds (`research/`,
`video/`) and are installed by their own skills; the `docs` kind is for
everything else. Then link the installed document from the epic's
`## References` shelf. When the change has no resolving epic, cite the
document in `plan.md` prose instead and edit no epic. A file already living
under the content dir's `research/`, `video/`, or `docs/` folder is read and
linked as-is — nothing is reinstalled.

### 3. Durable — outlives the feature

Knowledge that will still be true after this epic ships and after its code is
rewritten: a standing engineering position, a cross-feature convention, a
workspace fact about how this organization works. Its home is the workspace
wiki — distilled there by `/s:teach`, or filed to the oracle queue for a
human to answer (`wiki-queue-answer` / `wiki-queue-discard`).

**The queue write is not this rubric's decision.** Once an item is classified
durable, the capture durability rubric
(`plugins/s/skills/ask/references/capture-rubric.md`) governs whether and how
it is captured — its tiers, examples, and consent rule are authoritative
there and are not duplicated here. This rubric only says *the wiki is where
this belongs*; that one says *whether the wiki keeps it, and with what
authority*.

Where no wiki resolves, say so in visible text — nothing durable was
captured — and carry on. A missing wiki never blocks the flow.

### 4. Noise — recorded nowhere, deliberately

Session logistics, scheduling remarks, vented frustration, exploratory
tangents that went nowhere, restatements of what a file already says.
Capturing these costs more than losing them: they dilute every later search
and read as standing positions when they were passing moods.

Noise means no **knowledge** capture. A plan's `## Questions and answers`
ledger may still record the resolution for the change itself — the ledger is
the change's record of its own conversation, not a knowledge store.

## Calibrated examples

| Arriving information | Tier | Why |
|---|---|---|
| "Drop the CSV export from this change — ship JSON only" | Binding | A mid-delivery scope cut; executors must not build the dropped surface. |
| "The importer must stay stdlib-only, no new dependency" | Binding | An executor-facing constraint that fails review if disobeyed. |
| "Every member must expose its verb through the existing CLI, not a new binary" | Binding | Binds every member change, so it is epic-scope — amend `## Decisions`, never a free edit. |
| A pasted product strategy memo the members should build in the spirit of | Reference | Informs judgment across the feature; nothing in it is a checkable constraint. |
| An excerpt of the third-party API's pagination contract | Reference | Consulted while implementing; the authority stays the vendor's docs. |
| Meeting notes recording why the vendor was chosen | Reference | Useful background for the feature's lifetime; not an instruction. |
| "Never hard-delete — soft-delete flags plus an audit log" | Durable | A standing engineering position that outlives this feature entirely. |
| "Async data accessors are named `fetch*`, never `get*`" | Durable | A cross-feature naming convention governing code not yet written. |
| "Support owns the runbook; ping #ops before any schema migration" | Durable | A workspace fact about how the organization works, true beyond this epic. |
| "I'm out Thursday, land this before then" | Noise | Session logistics; it steers today's sequencing and nothing after it. |
| "This build system is infuriating" | Noise | Vented frustration, not a position — capturing it would read as one later. |
| "Maybe we should have used Rust for the whole thing" | Noise | An exploratory tangent that changed nothing; the decision stands as recorded. |

## Tie-breakers

- **Binding versus reference: obeyed or consulted?** If ignoring it makes the
  work wrong, it is binding. If ignoring it only makes the work less
  informed, it is reference. A memo containing one hard constraint splits:
  install the memo as reference and record the constraint as binding.
- **Reference versus durable: tied to this feature's lifetime, or outliving
  it?** If the item becomes meaningless once this epic ships, it is
  reference; if it would still guide an unrelated feature next quarter, it is
  durable. A concrete artifact (a memo, an excerpt) leans reference even when
  its subject is broad — the shelf holds documents, the wiki holds positions.
- **Borderline cases lean toward the less-capturing, less-binding tier** —
  reference over binding, noise over durable. An un-captured item costs one
  future question; a wrongly captured one silently steers work, and a
  wrongly binding one blocks it.
- **Scope decides the binding tier's home.** Binding on this change alone →
  the member's `plan.md` and delta specs. Binding on every member → the
  epic's `## Decisions`, reached through the amendment discipline when the
  epic is already live, or written directly when the epic is still being
  authored.
