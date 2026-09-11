# docs-workspaces-rework
Status: verified
Epic: docs-rewrite
Theme: developer-experience

## Idea

Rewrite the flagship workspaces documentation cluster — `docs/workspaces.md`
plus the five part pages under `docs/workspaces/` — to the shipd documentation
standard, through the `/s:document` flow, so every page carries a doc-type
marker, fits its line cap, and passes `docs_lint.py` under the CI gate the
`docs-lint-gate` member already installed.

### Motivation

The cluster runs 1,013 lines across six files and none conforms to the
standard: no file carries a marker, `workspaces.md` (283 lines) mixes a
concept hub with ~200 lines of member-map and discovery-ladder reference, and
`teams.md` (200 lines) carries an enterprise example whose primary layout
contradicts the approved epic decision. The `docs-rewrite` epic names this
cluster the flagship — the model of the standard the other clusters follow.

### Details

- `docs/workspaces.md` becomes the concept index (≤100 lines); its two deep
  sections move to a new sixth part page, `docs/workspaces/member-map.md`
  (reference, ≤250 lines).
- The five existing part pages are rewritten in place to their assigned types
  and caps; no page is renamed or deleted.
- `teams.md`'s enterprise guidance is reshaped to the epic's decision, as the
  oracle confirmed: a dedicated workspaces repository holding one folder per
  team or group, each folder a job workspace, with per-group repositories
  kept as the explicitly-warned isolation escape hatch.
- `README.md`'s introduction gains the flagship link to the guide.
- The `shipd-workspace` capability's `workspaces-doc` requirement is modified
  to pin the six-part structure, the markers, and the enterprise guidance; a
  small `project-readme` requirement pins the README link.

### Non-goals

- No changes to the entry docs (`what-is-shipd.md`, `getting-started.md`,
  `quickstart.md`, `cheatsheet.md`) — they belong to the `docs-entry-merge`
  member, including `what-is-shipd.md`'s own workspaces-first link.
- No changes to the standard, the lint, the `/s:document` skill, or the CI
  step — fixed inputs per the epic.
- No changes to `docs/retros/`, and no other doc cluster.
- No engine or behavior changes — the rewrite documents what exists; every
  behavioral claim must survive restructuring or be dropped only as a
  duplicate of another page's statement, never corrected or extended.
- No change to the `workspaces-doc-examples` requirement's obligations —
  `multi-workspace-repos.md` keeps both shapes, its diagrams, tables,
  pros/cons, the plain-`git clone` direction, and the isolation warning.

## Implementation

**Target structure and classifications (binding):**

| file | type | cap |
| --- | --- | --- |
| `docs/workspaces.md` | concept (index) | 100 |
| `docs/workspaces/getting-started.md` | how-to | 150 |
| `docs/workspaces/member-map.md` (new) | reference | 250 |
| `docs/workspaces/nesting-and-stores.md` | reference | 250 |
| `docs/workspaces/teams.md` | how-to | 150 |
| `docs/workspaces/headless.md` | how-to | 150 |
| `docs/workspaces/multi-workspace-repos.md` | how-to | 150 |

**The `/s:document` flow governs every rewrite.** Read
`plugins/s/skills/document/references/standard.md` before writing; put the
marker on line 1; run
`python3 plugins/s/skills/document/scripts/docs_lint.py <file>` after each
rewrite and fix findings until it exits 0. Never restate the standard's rules
inside a doc.

**Content moves, it is not re-derived.** `member-map.md` receives the
"Mapping members to existing checkouts" and "Resolving from outside the
workspace" sections of today's `workspaces.md`, compressed to the standard:
the machine-local `.shipd-workspace.local.json` (both fields — `repos` and
`workspace_root`), the `workspace-map` list/set/remove verbs, the mapped
member's planner semantics (action `none`, drift notes, stale keys as notes,
malformed file failing the reading verb), and the three-rung discovery ladder
(ancestor search → pointer → origin-URL scan) with URL normalization, the
SSH-alias caveat, and the ambiguity warning naming the pointer remedy.

**Command convention.** Every interactive example invokes the `shipd` binary,
with three exceptions: `headless.md` (its contract is the binary-free read),
the index's usage example for the headless part, and `member-map.md`'s
`workspace-map` examples — the binary deliberately exposes no write verb, so
those verbs have no binary form. `member-map.md` leads with
`/s:workspace map` as the guided front door and presents the raw verbs as the
engine contract.

**Enterprise guidance in `teams.md` (oracle-settled, epic-decided).** Primary
layout: one dedicated workspaces repository for the organization, holding one
folder per team or group, each folder a job workspace — the multi-workspace
repo mechanics of `multi-workspace-repos.md`, linked rather than restated,
with partial materialization (sync only the members you use) and the member
map for checkouts that already exist. Escape hatch, stated in the same
section: a group whose knowledge must stay isolated gets its own workspace
repository, because git has no per-directory access control — separate repos
remain the isolation boundary. Keep projects-as-systems (projects follow
codeowner seams, never teams; a team is who works an initiative).

**`teams.md` keeps all verified coverage** while reaching 150 lines: several
engineers cloning one repo, machine-local members, the shared knowledge
surfaces, the stable gitignore block, the worktree-hooks consent gate with
`hooks trust`, the no-locks/no-networked-git concurrency expectations with
`queue.md` and `index.md` as conflict surfaces, duplicate `q-<slug>`
invalidity, single-`Answer:` conflict resolution, and the pull/push protocol.
Compression comes from the standard's terseness and from linking sibling
pages instead of restating them.

**Diagrams.** The cluster carries no mermaid diagrams today and gains none —
the ASCII layout trees (fenced code blocks) carry the topologies and stay,
labeled as today. The mermaid-diagram limits of the standard are therefore
trivially met.

**Links.** Intra-cluster: each part page opens with the back-link to the
index; `teams.md`'s current link to
`../workspaces.md#mapping-members-to-existing-checkouts` retargets to
`member-map.md`; every relative link and `#` anchor across the seven files
must resolve. Inbound: `docs/prd.md` and `docs/oracle.md` link
`workspaces.md`, whose path is unchanged. `README.md`'s introduction links
`docs/workspaces.md` immediately after the existing `what-is-shipd.md` link
and before any other link into `docs/`.

**Verification.** `python3 plugins/s/skills/document/scripts/docs_lint.py`
over all seven files exits 0 (the CI step then covers them on every PR);
`shipd lint docs-workspaces-rework` structurally validates the deltas.
