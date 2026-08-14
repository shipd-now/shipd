# memory-browse
Status: verified
Epic: personal-memory
Theme: developer-experience

## Idea

Add the two browse skills over the personal memory store: `/s:memory`, a
read-only list of the stored `memory-*` pages, and `/s:forget <description>`,
which locates the described memory, confirms removal with an AskUserQuestion, and
deletes it through `wiki-remove --personal`.

### Motivation

The epic shipped the personal store, taught the oracle to read it, and added
`/s:preferences` to write it — but a user still cannot see what has been
captured or remove a memory that is wrong or stale. This member closes that gap:
the read and remove halves of the personal-memory UX, both over machinery that
already exists (`cat wiki … --personal`, `wiki-remove --personal`).

### Details

- New skill `plugins/s/skills/memory/SKILL.md` (`/s:memory`): announce the
  plugin version, resolve the personal store with `wiki-show --personal`, read
  `cat wiki index --personal`, filter the catalogue to `memory-*` entries, and
  print them. Read-only: no mutation and no new engine verb. Report that no
  memories are stored when the store is empty or absent.
- New skill `plugins/s/skills/forget/SKILL.md` (`/s:forget <description>`):
  announce the version, resolve the store, locate the matching `memory-*` page by
  grepping the personal store's index and page bodies for the description's
  terms, confirm the removal with a single AskUserQuestion carrying the matched
  page's identity and summary, and — only on confirmation — remove it with
  `wiki-remove <slug> --personal`. No match removes nothing; multiple matches are
  disambiguated before the confirm. Carries the question-rejection-recovery rule.
- Add the `/s:forget` skill to the `shipd-interaction` question-rejection-recovery
  roster (seven → eight interactive skills); `/s:memory` is read-only and does
  not join.
- Add one-line `/s:memory` and `/s:forget` entries to the AGENTS.md roster.

Affected capabilities: `shipd-memory` (added — `memory-list-skill`, `forget-skill`),
`shipd-interaction` (modified — roster grows by one). Impact: new
`plugins/s/skills/memory/SKILL.md` and `plugins/s/skills/forget/SKILL.md`,
`AGENTS.md` roster sentence; plugin version bump to 0.6.24. No engine or script
changes — `wiki-remove --personal` and the `--personal` reads already exist. No
new dependencies.

### Non-goals

- No engine change — `/s:memory` reads the existing index and `/s:forget`
  drives the existing `wiki-remove --personal` verb; neither adds a CLI verb.
- No write/capture — capturing preferences is `/s:preferences` (the shipped
  `memory-capture` member).
- No content editing — `/s:forget` removes whole pages only; correcting a
  memory's text is a `/s:preferences` re-capture (update).
- No git-backing flow — that is the `memory-git-backing` member.
- No listing of the workspace or base wiki — memories live only in the personal
  store, so `/s:memory` lists that store alone.

## Implementation

- **`/s:memory` is a read-only index filter — no new verb.** It resolves the
  personal store via `wiki-show --personal`, reads `cat wiki index --personal`,
  keeps the `- [[memory-<subject>]] — <summary>` entries (slug prefix `memory-`),
  and prints them. When `wiki-show --personal` reports no store, or the store
  holds no `memory-*` page, it reports that no memories are stored and mutates
  nothing. Rejected: a dedicated `wiki-list` engine verb (the index already is
  the catalogue; listing is a pure read the skill does directly).

- **`/s:forget` follows locate → confirm → remove.** It resolves the store,
  then locates the target by reading `cat wiki index --personal` and grepping the
  personal store's `wiki/` dir (the directory `wiki-show --personal` prints) for
  the description's terms. On exactly one match it issues a **single
  AskUserQuestion** in a prose-free turn (the matched page's slug and summary
  carried inside the dialog's fields, per the dialog-and-prose-separation rule)
  and, only on an affirmative selection, runs `wiki-remove <slug> --personal`.
  On no match it reports the miss and removes nothing; on multiple matches it
  presents the candidates for the user to pick before the confirm. Rejected: a
  typed confirmation round (the epic binds `/s:forget`'s confirm to
  AskUserQuestion — a destructive action gets a deliberate dialog).

- **`wiki-remove` does the safe deletion.** The verb (shipped in
  `personal-memory-store`) removes the page, drops its index entry, appends a
  dated `remove` log line, runs the whole-store wiki lint, and restores
  byte-for-byte on any finding — so `/s:forget` inherits the stranded-`[[link]]`
  refusal and reserved-slug guard without reimplementing them. `/s:forget` only
  decides *which* slug and *whether* the user confirmed.

- **`/s:forget` joins the interaction roster.** Because it issues an
  AskUserQuestion, its SKILL.md carries the question-rejection-recovery rule and
  the `shipd-interaction` roster requirement grows from seven to eight skills. Both
  browse SKILL.md files follow the existing plugin skill conventions (frontmatter
  with trigger phrases, a version-announce first status sentence); `/s:memory`,
  being non-interactive, does not join the roster.

Risk: `/s:forget`'s locate could match the wrong page on a vague description;
guarded by the mandatory confirm (the user sees the exact slug and summary before
deletion) and the multiple-match disambiguation step. A skill-only change is
exercised by a real drive against a throwaway `memory_dir` (list, then
locate-confirm-remove), and — per AGENTS.md — warrants a local eval run before
shipping (the eval harness does not yet cover these skills, so this is manual).
