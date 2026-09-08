# prd-discovery
Status: active
Theme: developer-experience

## Introduction

shipd's delivery machinery is strong from decomposition onward — initiatives
capture outcome goals, epics decompose features, changes plan and ship them —
but the **discover phase** of product engineering has no artifact at all. The
thinking that precedes an epic (what problem, for whom, why now, what does
success look like, what are the constraints and open product questions) lives
in the user's head or in ad-hoc conversation, and every epic authoring session
re-derives it. There is also no way for a skill to *find* the material that
thinking should rest on: `shipd related` ranks only spec artifacts and wiki
pages, so the codebase itself and workspace-level knowledge stay invisible to
retrieval.

This epic adds the discover phase as a first-class workspace artifact: the
**PRD**. A new `/s:prd` skill interrogates the user — deliberately more
aggressively than the single-round house style — until a Product Requirements
Document can be written against one of three plugin-shipped templates (basic,
standard, comprehensive; standard is the default, and the skill may escalate
or de-escalate the tier as the discovered complexity warrants). PRDs live in
the workspace beside initiative briefs, are written only through the engine's
staged, lint-gated emit path, and feed decomposition: an epic can carry an
optional `PRD:` metadata line, closing the loop
Initiative → PRD (discover) → Epic → Change. Grounding the interrogation, a
new `shipd search` verb generalizes `related`'s ranked term-hit engine to also
cover the invoking repo's git-tracked code files and the workspace-level
surfaces (wiki pages, initiative briefs, PRDs), so the skill investigates
before it grills.

Intended outcome: a product idea enters the workspace as a lint-clean PRD that
an epic can cite, authored from an interview grounded in what the codebase,
docs, research, and wiki already know.

Success criteria:

- `/s:prd` produces a PRD that passes the engine lint on the first install,
  stored under the workspace's content directory and readable back through an
  engine `cat` verb.
- The standard template is the default, and the skill can justify and switch
  to basic or comprehensive mid-interview without restarting.
- `shipd search <terms>` returns ranked hits spanning spec artifacts, wiki
  pages, workspace initiatives/PRDs, and the repo's tracked code files, with
  `--json` for scripting, while `shipd related` behaves exactly as before.
- An epic carrying `PRD: <slug>` lints clean and the link resolves through
  the workspace chain.

### Non-goals

- **No PRD → epic auto-decomposition.** `/s:prd` ends at the installed PRD;
  turning it into an epic remains a separate, user-initiated `/s:epic` run
  that reads the PRD as context.
- **No workspace-customizable templates.** The three templates ship in the
  plugin and version with it; per-workspace template overrides are
  deliberately deferred.
- **No cross-repo code search.** `shipd search` covers the invoking repo's
  tracked files plus workspace-level knowledge surfaces; it does not walk the
  workspace's other declared project repositories' code.
- **No semantic or embedding search.** The search verb stays stdlib-only,
  case-insensitive term-hit ranking — the same scoring family `related`
  already uses.
- **No new third-party dependencies.** Everything lands under the engine's
  stdlib-only constitution.

## Decisions

- **PRDs are workspace artifacts that feed epics.** A PRD lives at
  `<workspace-root>/<content-dir>/prds/<slug>/prd.md`, resolved and written
  exclusively by the engine (mirroring initiative briefs — never a hand-built
  path, never a direct write). An epic may carry an optional `PRD: <slug>`
  metadata line, giving the hierarchy a discover rung:
  Initiative → PRD → Epic → Change. A PRD may optionally name its parent
  initiative in its own header.
- **The search function is a new `shipd search` verb, not an extension of
  `related`.** It generalizes `related`'s ranked, case-insensitive term-hit
  scorer over a superset corpus: the existing spec surfaces, plus the
  invoking repo's git-tracked files, plus the workspace-level surfaces
  (wiki pages — the store whose `index.md` catalog grammar the ranked output
  echoes — initiative briefs, and PRDs). `related` keeps its exact current
  contract for `/s:fix` retrieval. `search` prints the same keyed-block
  ranked format with a `--json` mode and is exposed through the binary's
  curated verb table as a read-only verb.
- **The plugin owns the three templates.** `basic`, `standard`, and
  `comprehensive` live as references under `plugins/s/skills/prd/references/`,
  versioned with the plugin. The PRD header records the chosen tier in a
  `Template:` line; the linter validates the document against that tier's
  required-section contract, kept as an engine-side registry so the linter
  never parses template prose. `standard` is the default tier.
- **The interview is multi-round grilling — a deliberate exception to the
  single-batched-round house style.** `/s:prd` investigates first (search
  verb, spec surfaces, wiki), then runs successive AskUserQuestion rounds
  section by section until the active tier's contract is covered, escalating
  or de-escalating the tier as discovered complexity warrants. The
  codebase-first rule still binds: nothing discoverable is ever asked.
- **All engine additions are stdlib-only Python 3** with unittests under
  `plugins/s/skills/build/tests/`, and every change touching `plugins/s/`
  bumps the plugin version in the same PR.
- **One staged write path.** The PRD installer is a `spec_emit.py prd` verb
  over a throwaway staging directory — backup, install, whole-surface lint,
  byte-for-byte restore on any finding — exactly the wiki/initiative emit
  discipline. The skill never writes the store directly.

## Design

The feature is four layers, built bottom-up:

1. **Retrieval** (`shipd-search`): `spec_status.py` gains a `search` verb
   reusing `_related_score` and the `related` corpus builders, extended with
   two new surfaces — git-tracked repo files (enumerated via `git ls-files`,
   binary-ish files skipped) and the workspace-level artifacts (initiative
   briefs and, once the store exists, PRDs; wiki pages are already in the
   corpus). The binary's `VERB_TABLE` maps `search` to it. This lands first
   so the skill and later members can rely on it.
2. **Store** (`prd-store`, `prd-templates`, `prd-emit`): `spec_common.py`
   gains the PRD path helpers and header grammar (Status vocabulary
   `draft`/`approved`/`superseded`, `Template:` tier, optional
   `Initiative:`); `spec_lint.py` gains `lint_prd`, validating the header and
   the tier's required-section contract from the engine-side tier registry;
   the three template files ship as skill references whose section skeletons
   match that registry (a drift-guard test keeps them aligned);
   `spec_emit.py` gains the staged `prd` install verb and `spec_status.py`
   the read verbs (`cat prd <slug>`, a `prd`-aware `locate`/list surface),
   both exposed through the binary.
3. **Hierarchy link** (`epic-prd-link`): the epic linter accepts an optional
   `PRD: <slug>` metadata line and verifies the slug resolves to a PRD
   through the workspace chain; `epic-show` reports it; `/s:epic`'s contract
   documents it.
4. **Skill** (`prd-skill`, `prd-doc`): `/s:prd` orchestrates — announce
   version, search-first investigation, multi-round tier-aware interview,
   compose against the active template, install through the emit verb, lint
   gate, stop. A harness body makes the command portable, and the
   documentation change records the discover phase in the workspace docs.

Seams: retrieval is independent of the store; store precedes emit, link, and
skill; the skill consumes everything below it. Each member is one worktree,
one branch, one PR, and each `plugins/s/` PR carries its own version bump.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| shipd-search | New `search` verb in `spec_status.py` + binary: `related`'s ranked term-hit scorer over the superset corpus (spec surfaces, wiki, initiatives, PRDs, git-tracked repo files), keyed-block output with `--json`, unittests | high | medium | medium | medium |
| prd-store | Engine foundation: PRD path helpers and header grammar in `spec_common.py` (Status/Template/Initiative), tier registry, `lint_prd` in `spec_lint.py`, unittests | high | medium | medium | medium |
| prd-templates | The basic/standard/comprehensive template references under the prd skill, section skeletons matching the tier registry, drift-guard test | low | low | low | low |
| prd-emit | Staged `spec_emit.py prd` install verb (backup → lint → restore) + `spec_status.py` read verbs (`cat prd`, list) + binary exposure, unittests | medium | medium | low | medium |
| epic-prd-link | Optional `PRD: <slug>` epic metadata line: linter acceptance + workspace-chain resolution check, `epic-show` reporting, `/s:epic` contract note | low | medium | low | low |
| prd-skill | `/s:prd` SKILL.md + harness body: search-first investigation, multi-round tier-aware interview contract, template escalation rules, emit + lint gate ending | medium | medium | medium | medium |
| prd-doc | Documentation: the discover phase and PRD artifact in the workspace docs (concept, storage, lifecycle, `shipd search` usage) | low | low | low | low |

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 154 | 29.4k |
| Edit | 25 | 10.1k |
| Read | 33 | 5.4k |
| (no tool) | 0 | 4.2k |
| Agent | 4 | 2.0k |
| Monitor | 1 | 17 |
| ToolSearch | 1 | 6 |
| **Total** | 218 | 51.2k |
