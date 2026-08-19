# /s:teach — reference

The fuller protocol behind the teach command's workflow: the
ledger-correction mode, the page grammar, queue draining, and promotion.

## Ledger-entry correction — `<change> Q<n>`

An argument of the form `<change> Q<n>` (e.g. `dark-mode-toggle Q1`) points
at one recorded consultation in that change's plan ledger and bypasses the
distillation sweep entirely.

1. Resolve the store exactly as the sweep does.
2. `cat change <change>` — it resolves a planned change first and falls
   back to the newest archived copy, so a merged change stays readable.
3. Print the `### Q<n>` entry in full — its header and every field
   (`**Question:**`, `**Verdict:**`, `**Answered by:**`, `**Answer:**`, and
   the `**Cited:**` or `**Queued:**` field) — before correcting anything.
4. One typed round: what the standing answer should be instead, and what
   the correction rests on.
5. Install through the staged emit, with three rules specific to this mode:
   - update the page the entry **Cited** (when it exists) rather than
     adding a near-duplicate slug;
   - stage the user's correction verbatim as a dated `sources/` file;
   - drop the entry's `Queued: q-<slug>` block from the staged `queue.md`.
     A block already gone is not an error.

A missing change, or a ledger with no `Q<n>` of that number, stops the run
without writing anything — no staging dir, no emit, no queue write.

## Page grammar

Pages follow the store's own `schema.md` (`cat wiki schema`): kebab-case
`wiki/<slug>.md`, `[[slug]]` wikilinks that resolve **within the same
store**, and one `- [[slug]] — <summary>` index entry per page. Every page
names the repo artifact behind its position (`epic/<slug>`,
`verified/<capability>`, `research/<slug>`) so a reader can verify it.

Repo artifacts are never copied into `sources/` — the repos already hold
them durably, and `sources/` is add-only, so a copy would refuse a refresh.
`sources/` is for interview and drained-queue answers, which exist nowhere
else.

## Bounds

One run touches at most 15 pages (5–15 is the working band), decision-dense
surfaces first. The `log.md` entry records what was covered so a later run
continues where this one stopped.

## Queue draining

`cat wiki queue`, then for every `## q-<slug>` block whose `Answer:` line is
not `pending`: distill the answer into page content and remove the block
from the staged `queue.md`. Pending blocks stay untouched — the queue is a
pending-only worklist. Name each drained `q-<slug>` in the log entry.

## Promotion to a base store

Only when `wiki-show` reported `base: <path> (present)`. Classify each page
and drained answer as job-scoped (default) or job-independent; offer each
job-independent item for promotion in the single interview round, with
promotion as the recommendation. On `base: none` or `(absent)`, skip
classification and offer no promotion.

Accepted promotions install through a **second, separate** staged emit:

```
python3 "$S/spec_emit.py" --root <base-store-path> wiki --from "$base_staging"
```

That staging dir holds only the promoted `wiki/<slug>.md` pages, the base
store's **own** full `index.md` (read with `--root <base-store-path> cat
wiki index`) and `log.md`, and any backing answer as a dated `sources/`
file. Promoted pages land in the base store **only** — never also in the
job store's staging — and promotion never removes an existing job-store
page.

## What the emit accepts

`index.md`, `log.md`, `queue.md`, `wiki/<slug>.md`, and `sources/<file>`.
It backs up the affected files, installs the staged set, lints the whole
store, and restores byte-for-byte on any finding — so a failed run
installed nothing. Fix the staged files and re-run.
