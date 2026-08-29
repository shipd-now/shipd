# .shipd/ — the shipd spec library

This directory is the on-disk home of shipd's LLM-free spec engine. It holds
the canonical (master) specifications, the in-flight change artifacts, and the
applied changes. The engine (`spec_merge.py`, `spec_lint.py`,
`spec_common.py`, under `plugins/s/skills/build/scripts/`) is exact-keyed CRUD
over the markdown described here — no language model reads or writes these files.

## On-disk layout

```
.shipd/
  README.md                      this document — the spec grammar authority
  constitution.md                optional steering rules (binding when present)
  verified/                      master library — the single source of truth
    <capability>/
      spec.md                    one file per capability
  planned/                       in-flight changes (not yet merged)
    <change>/
      plan.md                    idea (why + what) + implementation decisions
      tasks.md                   the implementation checklist
      specs/
        <capability>/
          spec.md                delta spec for each affected capability
      artefacts/                 optional: standalone planning outputs
        <file>                   referenced from plan.md, tasks.md, or a delta
  completed/                     applied changes, retained immutably
    <date>-<change>/             moved here by spec_merge after a merge
      ...                        the change's full artifact set
  epics/                         feature decompositions grouping member changes
    <slug>/
      epic.md                    Introduction + Decisions + Design + stub table
  research/                      home of cited research reports epics link
    <slug>/
      report.md                  title + themed findings + numbered ## Sources
  video/                         home of video intent briefs
    <slug>/
      brief.md                   Video: header + Speakers/Intents/Sources
```

- `.shipd/verified/<capability>/spec.md` is the **master library**: the current,
  canonical definition of every requirement, one file per capability. The merge
  engine reads and writes only these files.
- `.shipd/planned/<change>/` holds a change under construction. Every change
  carries the **lean artifact set** (`plan.md`, `tasks.md`, and a delta
  `specs/<capability>/spec.md` per affected capability), regardless of size,
  and MAY additionally carry an `artefacts/` directory of standalone planning
  outputs (see [Artefacts](#artefacts)).
- `.shipd/completed/<date>-<change>/` retains a change after its delta has
  been merged, so applied changes are auditable and never re-merged. It is a
  sibling of `.shipd/planned/`, which therefore holds only live changes.
- `.shipd/epics/<slug>/epic.md` holds an **epic**: the grouping layer above a
  change. An epic records the cross-cutting decisions and design of a feature
  too large for one change, and decomposes it into a table of member changes.
  Members are planned later, one at a time, each born in its own worktree via
  `/s:plan` carrying an `Epic: <slug>` line (see [Epics](#epics)).

### The plan document

`plan.md` is the single decision-driving document for a change. It begins with a
`# <change>` title on line 1 (matching the change's directory slug) and a
`Status: <status>` line as the first non-blank line after it. The status value is
one of `draft`, `ready`, `active`, `complete`, `verified`, or `rejected`
(`rejected` is the context-sufficiency gate's parking state — see below). The
document then holds two required level-2 sections:

- **`## Idea`** — opens with a **one-sentence summary** of the change, then a
  required `### Motivation` subsection (at most two sentences on **why** the
  change is being made, grounded in the planning context — never a guess), then
  a required `### Details` subsection (the concrete **what** — the changes plus
  the affected capabilities and impact), then a required `### Non-goals`
  subsection last, listing the scope exclusions. There is no "Goals" section:
  the Idea *is* the goals.
- **`## Implementation`** — the binding technical decisions ADR-style (each with
  a rationale and, where useful, the rejected alternative) and the risks (the
  "how").

Both sections SHALL be present, in that order; additional sections MAY follow.
The linter enforces the header, the two level-2 sections, and the presence of
the `### Motivation`, `### Details`, and `### Non-goals` subsections (presence
only — the subsection order and the summary/motivation length limits stay
authoring guidance). `tasks.md` stays a separate file so executors can flip its
checkboxes during a build without rewriting `plan.md`.

A single **gate-owned `## Context insufficient` section** MAY precede `## Idea`.
It is written and removed only by the context-sufficiency gate
(`spec_gate.py <change>`): on a failing gate run it holds a summary paragraph and
one dot-point per finding (a stale `base:` hash, a placeholder marker, an
unresolvable task file reference, or a delta targeting a nonexistent capability),
and the change's status becomes `rejected`; a human enriches the plan and
re-gates, at which point a passing run removes the section and promotes the plan
to `ready`. The linter tolerates the section in any status.

### Artefacts

A change MAY carry an optional `artefacts/` directory holding the standalone
outputs of planning — a policy document, a block of verbatim text, any content
that must be preserved exactly rather than paraphrased into the lean artifact
set. Every file inside it MUST be referenced by its change-relative path
(`artefacts/<file>`) from at least one of `plan.md`, `tasks.md`, or a delta
spec; the linter errors on any file it is not (`spec_lint.py`'s
`check_artefact_references`), so an orphaned artefact blocks the install. The
directory travels with the change through installation and through the merge's
archive to `.shipd/completed/<date>-<change>/artefacts/`.

### The questions-and-answers ledger

An optional **`## Questions and answers` section** MAY follow the required
sections. It is the durable record of the oracle consultations that ran
while planning the change: one entry per consultation, in consultation order,
so a settled decision keeps a stable `Q<n>` reference long after the session
ends. A planning session with no consultation emits no section.

Each entry is a level-3 header followed by a dash list of fields:

```
### Q1: Which store holds the toggle?
- **Question:** Should the toggle live in the settings store or the theme
  store? Options: (1) settings; (2) theme. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** The settings store — option 1. It already persists user-scoped
  display preferences.
- **Cited:** verified/settings-store
```

- **`### Q<n>: <one-line question summary>`** — entries are numbered
  sequentially from `Q1`; enrichment-time consultations append to the existing
  section and continue the numbering.
- **`**Question:**`** — the full compact question as it was put to the oracle
  (decision, options, recommendation).
- **`**Verdict:**`** — `ANSWER` or `INSUFFICIENT`.
- **`**Answered by:**`** — `ORACLE` or `USER`, placed directly above the answer
  so who settled the decision is clear at a glance.
- **`**Answer:**`** — the oracle's position in full for an `ANSWER` entry, the
  user's typed resolution for an `INSUFFICIENT` one.
- **`**Cited:**`** — the oracle's sources; on `ANSWER` entries.
- **`**Queued:**`** — the `q-<slug>` the oracle filed in the wiki queue; on
  `INSUFFICIENT` entries.

The linter validates the section when it is present — at least one entry,
`### Q<n>:` headers numbered sequentially from `Q1`, and a `**Question:**`,
`**Answered by:**`, and `**Answer:**` field on every entry — and reports
nothing when it is absent. Entries are paraphrased rather than pasted so they
never carry the context gate's placeholder markers or its open-question phrase,
which the gate scans for across the whole plan. `/s:teach <change> Q<n>` replays
an entry so the user can correct the oracle's standing answer.

### Header metadata

The header MAY carry an optional **metadata block**: contiguous `Key: value`
lines immediately after the `Status:` line, ended by the first blank line or
heading. A plan with no metadata block behaves exactly as it did before this
feature — the block is purely additive.

```markdown
# csv-export
Status: draft
Profile: lite
Epic: reporting-overhaul
Theme: reliability
```

Exactly four keys are recognized; every value is a **kebab-case slug**. An
unrecognized key in the block (e.g. a `Them:` typo) or a non-kebab value is a
lint error.

- **`Profile:`** — `full` or `lite`; absent means `full`. `lite` **relaxes
  content expectations only** (brevity, optional test-first task ordering); it
  does **not** change the required artifact set or any structural lint rule.
  Every change carries `plan.md`, delta specs, and `tasks.md` regardless of
  profile.
- **`Epic:`** — the slug of the epic this change belongs to.
- **`Initiative:`** — the strategic initiative this change serves. A change
  that carries `Epic:` **must not** also carry `Initiative:` — a grouped change
  derives its initiative *through* its epic. Only a standalone change (no
  `Epic:`) may carry `Initiative:` directly; declaring both is a lint error.
- **`Theme:`** — a cross-cutting theme slug (see the theme vocabulary below).

The status CLI preserves these lines: `set-status` and `sync` rewrite only the
`Status:` line, leaving the metadata untouched, and `show` prints the
recognized metadata lines alongside the status and task progress.

### Theme vocabulary — `.shipd-config.json`

`.shipd-config.json` is optional, stdlib-JSON repo configuration at the library
root. When it declares a non-empty `valid_themes` array, a plan's `Theme:`
value is validated against that vocabulary; a theme outside it is a lint error.
When the file is absent or declares no `valid_themes`, any kebab-case theme is
accepted. A file that exists but is not valid JSON is a lint error naming the
file.

```json
{
  "valid_themes": ["developer-experience", "reliability", "spec-engine"]
}
```

### The autonomous pipeline — the `autonomous-pipeline` key

`.shipd-config.json` MAY declare an `autonomous-pipeline` key: an **ordered JSON
list that _is_ the delivery pipeline**. The stage registry — in canonical
relative order — is `research → epic → plan → gate → build → review`. Each list
entry is exactly one of five forms:

```json
{
  "autonomous-pipeline": [
    { "stage": "research" },
    { "stage": "plan",
      "tools": [{ "name": "mcp:sourcebot", "fallback": "builtin" }] },
    { "stage": "gate", "skip": true },
    { "custom": "deploy-preview", "command": "scripts/preview.sh" },
    { "stage": "build" },
    { "stage": "review",
      "replace": { "command": "my-ci review", "fallback": "skip" } }
  ]
}
```

- `{ "stage": "<name>" }` — run a registry stage as built in.
- `{ "stage": "<name>", "skip": true }` — explicitly skip it (the visible-in-file
  variant of omission).
- `{ "stage": "<name>", "tools": [...] }` — bind additional tools to it; each
  tool names a `fallback` of `builtin` or `skip`.
- `{ "stage": "<name>", "replace": {...} }` — substitute its implementation with
  a `command` or a `tool`, carrying a `fallback` of `builtin` or `skip`.
- `{ "custom": "<kebab-name>", "command": "<command>" }` — insert a custom step
  at that list position.

A declared list is **wholesale**: stages absent from it do not run, and that
omission is legitimate — including for gates (declaring the key is the required
explicitness). Built-in stages that _are_ listed must appear in the canonical
relative order above; `custom` steps may sit at any position. `skip` may only
be `true` when present, and a skipped entry carries **no other field** beyond
`stage` — options on a skipped stage are an error, not a silent no-op. `tools`
and `replace` are mutually exclusive on one entry. Entries are validated
**strictly**: a key not defined for the entry's form is rejected as unknown,
and a wrongly typed value (`{"skip": 1}`, `{"parallelism": "2"}`) is rejected
rather than coerced. **When no layer declares the key, the pipeline is the
built-in default: every registry stage in canonical order, unskipped and
unbound.** Like every top-level key, `autonomous-pipeline` merges
**nearest-wins-wholesale** — the closest layer declaring it wins the whole key.
Inspect the effective pipeline and its provenance with
`spec_status.py pipeline-show`.

Validation runs on **pydantic**: a declared entry list — and every preset but
`default` — is checked against the engine's pipeline schema, and when pydantic
is not importable resolution **fails closed**, naming pydantic, the config file
that declared the key, and the `pip install -r requirements.txt` remedy. It
never falls back to weaker validation. The absent key and the `"default"`
preset resolve with no third-party package at all.

#### Per-stage options

An unskipped entry may carry typed options beside its form:

- **Every stage entry** — `model`: a non-empty string that is either a symbolic
  tier (`session`, `tier-below`, `tier-two-below`, resolved relative to the
  driving session) or a concrete model id. The set of concrete ids is open, so
  any other non-empty string is taken as one.
- **`build`** — `subagent_model` (same tier type as `model`), `validator`
  (boolean, default `true`), `telemetry` (boolean, default `true`), and
  `parallelism` (integer >= 1).
- **`review`** — `disposition`: one of `all`, `high-only`, or `none` (default
  `all`); the set is closed.
- **Any stage or custom entry** — `autopilot`, an object of driver knobs:
  `attempts` (integer >= 1, default 3), `timeout` (integer > 0), and
  `max_resumes` (integer >= 0). Unknown keys inside it are rejected like
  anywhere else.

```json
{
  "autonomous-pipeline": [
    { "stage": "plan", "model": "session" },
    { "stage": "gate", "autopilot": { "attempts": 1 } },
    { "stage": "build", "validator": false,
      "subagent_model": "tier-two-below", "telemetry": false },
    { "stage": "review", "model": "tier-below", "disposition": "high-only" }
  ]
}
```

Defaults are **schema-declared and never injected**: a resolved entry carries
exactly the keys its author wrote, so `{ "stage": "build" }` resolves to
`{ "stage": "build" }` — not to an entry with `validator` and `telemetry`
spelled out — even though those defaults govern the run.

#### Preset names — the one-line form

Instead of a list, the key MAY hold a **string naming a built-in preset**:

```json
{ "autonomous-pipeline": "eco" }
```

The shipped presets are:

- `default` — every registry stage, bare, in canonical order: exactly the
  pipeline you get with the key absent, resolved without pydantic.
- `eco` — the cheap delivery: `research` and `epic` skipped, `plan` on the
  session model, `gate` with one autopilot attempt, `build` without the
  validator on a two-tiers-below subagent model and without telemetry,
  `review` a tier below with `high-only` disposition.
- `basic` — cheaper still: `eco` with the gate skipped, `build`'s subagent
  model one tier below, and telemetry left on.

Every shipped preset keeps `plan` on the session model and keeps an **unskipped
review** — the cheap presets cheapen review through its `model` and
`disposition`, never by dropping it.

The key holds **a preset name or a list, never both**: presets do not merge
with overrides. To start from a preset and tweak it, print it and commit the
result as your own list — `spec_status.py pipeline-show --expand eco` prints
the preset's entry list as JSON, which is exactly what the key accepts.

An unknown preset name is an error naming the known presets and the config file
that supplied it. Every preset but `default` expands through the same pydantic
validation a declared list gets, so it fails closed with an install hint when
pydantic is not importable; `default` and `--expand default` need no
third-party package at all. A preset-resolved pipeline reports its provenance
as `preset:<name> (<config-path>)`.

### PR mode — the `pr-mode` key

`.shipd-config.json` MAY declare a `pr-mode` key: the string `auto` or the
string `draft`, and nothing else.

```json
{ "pr-mode": "draft" }
```

**When no layer declares the key the mode is `auto`** — today's behavior, where
a change ships as an auto-merging PR. Like every top-level key, `pr-mode`
merges **nearest-wins-wholesale**, so declaring it once at a **workspace root**
governs every member repo beneath it; a member repo declaring its own value
overrides that for itself. A *declared* value that is neither `auto` nor
`draft` is an error naming the key, the offending value, the accepted values,
and the config file that supplied it — `shipd doctor`'s `config` check surfaces
it, and every consuming flow stops rather than guessing. Inspect the effective
value and its provenance with `spec_status.py config-show`.

The mode governs **change-shipping PRs only** — the build ship phase and the
autopilot's members. **Metadata PRs keep auto-merging regardless**: epic-close
status derivations and initiative tagging are unaffected by the mode.

Under `draft`, a shipping change opens its PR **as a draft**
(`gh pr create --fill --draft`) and **no auto-merge is armed**. The
semantic-review gate is still posted and its findings still dispositioned, but
the merge watch and the merged close-out (worktree pruning, the `main` pull,
the epic derivation) do not run: **the open draft PR is the terminal state**,
reported with its full URL, with the worktree and branch left in place and
merging left to a human. Such a member is recorded with the terminal outcome
`drafted`, which the delivery board lanes under `review` with a `◇ drafted`
badge — awaiting a human, never laned as shipped on the board.

### Guardrails — the rulebook and the `guardrails` key

The plugin ships a **guardrail hook** that runs around every `Edit` and `Write`
tool call and matches the lines the call would *add* against a rulebook. Only
added lines are evaluated: a line present in both an Edit's `old_string` and
its `new_string` is never re-flagged.

Each rule declares one of two **modes**, which decide when it is consulted and
what a match produces:

| Mode | Runs on | Effect |
| --- | --- | --- |
| `deny` (the default) | `PreToolUse`, before the call | the call is **blocked** with the rule's message, so the unwanted line never lands |
| `remind` | `PostToolUse`, after the call | the edit **stands** and the rule's message reaches the model as context |

Use `deny` for lines that must not exist and `remind` for guidance too fuzzy to
block on.

#### The rule file format

A rule is a markdown file `<name>.md` — the filename stem is the rule's name,
and what a deny reason or reminder cites. It opens with a frontmatter block
between `---` lines, read as flat `key: value` pairs (split on the first colon,
unknown keys ignored), and everything after the block is the rule's corrective
message:

```markdown
---
pattern: console\.log\(
mode: remind
files: *.js, *.ts
cooldown: 600
---
Use the logger, not console.log — it carries the request id.
```

| Key | Meaning |
| --- | --- |
| `pattern` | **required**; Python `re` syntax, applied per added line with `re.search`. Written plainly — no JSON double-escaping |
| `mode` | `deny` when absent, or `remind` |
| `files` | optional comma-separated `fnmatch` globs tested against the call's `file_path`; a rule with `files` applies only where a glob accepts the path |
| `cooldown` | optional positive integer seconds, meaningful only with `mode: remind` |

The message body must be non-empty. A file that declares no `pattern`, carries
an empty body, names an unrecognized `mode`, or whose pattern does not compile
is **skipped**, and the rest of the rulebook keeps loading.

A `remind` rule fires **once per session** by default, so a standing note never
becomes noise. Declaring `cooldown: <seconds>` re-arms it that many seconds
after its last fire instead. The per-session record lives under
`~/.shipd/guardrails/`, whose state files from past sessions are removed
automatically about a week after their last use.

#### Where rules come from

The registry merges three sources, **deduplicated by rule name with the first
source winning**:

1. **The repo** — `<content-dir>/rules/*.md` in each ancestor directory of the
   working directory, nearer ancestors first (`.shipd/rules/` by default, or
   whatever the `dir` key names).
2. **The user** — `~/.shipd/rules/*.md`, applying in every repository.
3. **The plugin** — its own `hooks/rules/*.md` built-ins.

So a repo rule overrides a user rule overrides a built-in **by name**: dropping
a `changelog-comment.md` into `.shipd/rules/` replaces the built-in of that
name wholesale, pattern and message together.

**Three built-in rules are active in every repository** unless a source
overrides or a config layer disables them:

| Rule | Denies |
| --- | --- |
| `changelog-comment` | comments narrating the edit — `// Fixed: off-by-one` |
| `narrating-comment` | step narration — `# now we build the index` |
| `filler-placeholder` | elisions standing in for content — `// ... rest of the file` |

They are ordinary rule files, readable and copyable as templates for your own.

#### The `guardrails` config key

Rules are authored as files; the config key holds only the **kill-switches**.
`.shipd-config.json` MAY declare `guardrails` in either of two forms. The
boolean `false` turns the hook off wholesale — no source is consulted and every
call is allowed:

```json
{ "guardrails": false }
```

Or an object whose one recognized member is `disable`, a list of rule names
dropped after the sources merge:

```json
{ "guardrails": { "disable": ["narrating-comment"] } }
```

An earlier version of this key also accepted a `rules` member holding rule
objects. **The rulebook supersedes it**: a `rules` member is now ignored
without erroring, and any such rule should be moved to a file under
`<content-dir>/rules/` or `~/.shipd/rules/`. Like every top-level key,
`guardrails` merges **nearest-wins-wholesale** — declaring it at a workspace
root governs every member repo beneath it, and there is no deep merge, so a
member repo's declaration replaces the root's entirely.

The hook **fails open**: a declared value that is neither `false` nor an object
is treated as undeclared rather than erroring, a malformed or uncompilable rule
is skipped while the rest stay active, cooldown-state failures still let the
reminder through, and any unexpected failure allows the call. Setting the
environment variable `SHIPD_GUARDRAILS` to `off` bypasses the hook entirely for
that session — the emergency escape hatch when a rule misfires.

### Context economy

`plan.md` and each delta spec should stay under **~2,000 tokens** (roughly
8,000 characters). The linter warns — never errors — when a file exceeds that
budget; an oversized document is a nudge to decompose the change into smaller
ones, not a structural failure.

### Workspace — the `workspace` key of `.shipd-config.json`

A **workspace** groups one or more repos above the library. It is declared by a
`workspace` key in the workspace root's `.shipd-config.json`; that same object is
the registry, and the directory that holds it is the **workspace root**. The
engine finds the root by **nearest-ancestor discovery**: starting from a repo
and walking parent-by-parent to the filesystem root, the closest ancestor whose
`.shipd-config.json` declares `workspace` wins (the starting directory itself
included). No workspace is a normal state, not an error — the engine simply
reports that none was found, and requires no git repository along the way.

The registry (the `workspace` object) loads as a tolerant JSON object:
**unknown keys are preserved** untouched, leaving room for future workspace
state, and only a missing, unparseable, or non-object `workspace` value is an
error (which names the config file). Because the search is nearest-ancestor, the
declaration belongs **only at the intended workspace root** — a stray
`workspace` key in some parent directory's `.shipd-config.json` (e.g. in `$HOME`)
would be discovered instead.

### Projects — grouping repos within a workspace

A **project** groups repos under one focus. The registry's optional `projects`
key maps **kebab-case project slugs** to objects whose `repos` value is a list
of **workspace-root-relative path strings**:

```json
{
  "projects": {
    "alpha": { "repos": ["shipd", "apps/backend"] },
    "beta":  { "repos": ["apps/backend/service-x"] }
  }
}
```

- **Shape-only validation.** The registry is validated for shape, **never for
  existence**: a listed repo path absent on this machine is fine, because
  registries travel across machines. Validation checks that `projects` is an
  object, each slug is kebab-case, and each `repos` is a list of non-empty
  strings. The **one cross-project rule** is that a repo path listed by more
  than one project is an ambiguous-ownership error naming the path. Validate the
  registry directly with `spec_lint.py --workspace` (which resolves the
  workspace from `--root` and reports findings against `.shipd-config.json`);
  library and change lint stay registry-silent except where a brief's `Project:`
  line requires it.
- **Resolution by containment.** `project_of(workspace_root, path)` answers
  *which project owns this path*: the project whose repo entry equals or
  **contains** the path, the **longest (most specific) matching entry winning**
  across projects (so `alpha: apps` and `beta: apps/backend` resolve
  `apps/backend/repo-x` to `beta`). A path matching no entry resolves to the
  **implicit default project** — anonymous, unreferenceable by any slug, and the
  home of every repo no project claims.
- **Context.** `<workspace-root>/projects/<slug>/context.md` is reserved as
  **optional free-prose** steering context for a project. It is **never linted
  or required**; the status verbs simply surface whether it exists.
- **Viewing.** `spec_status.py workspace-show` prints the workspace root, each
  declared project (repos annotated `(absent)` when missing on this machine,
  plus `context.md` presence), and each initiative with its status and
  `Project:` scope, noting when the current repo falls under the implicit
  default. `spec_status.py project-show <slug>` narrows that to one project.

### Initiative briefs — `initiatives/<slug>/brief.md`

An **initiative** is the *why* layer of the Initiative → Epic → Change
hierarchy: the goal an epic or a standalone change is pursued in service of. Its
artifact is a **brief** living in the workspace (not the repo) at
`<workspace-root>/initiatives/<slug>/brief.md`:

```markdown
# mvp-readiness
Status: open
Project: alpha

Get the product ready for its first real users: the outcomes below are what
"ready" means, ticked off as they land.

## Requirements

- [ ] Onboarding works end to end
- [ ] The public API is documented
```

- **Header.** A `# <slug>` title matching the directory, and a `Status:` line
  whose value is one of `open`, `achieved`, `dropped`. An initiative is a goal:
  it is `open` while pursued, `achieved` when its requirements are all ticked,
  and `dropped` when abandoned (a manual, sticky act). There is **no** draft/
  ready pipeline — those are change-level statuses.
- **Metadata.** The optional header metadata block recognizes exactly one key,
  `Project:` (a kebab-case value scoping the initiative to a project). The value
  **must name a project slug declared in the workspace registry**; where the
  registry declares no projects, any `Project:` line is an error. A brief with
  **no** `Project:` line never loads the registry, but one that carries a
  `Project:` line also surfaces any registry-shape errors — a broken registry
  cannot silently pass a scoped brief.
- **Requirements as outcomes.** A required `## Requirements` section holds at
  least one `- [ ]` checkbox. These are **outcomes ticked over time, not
  tasks** — each line names something true of the finished goal, and the
  progress count (`initiative-sync`, `initiative-show`) is derived from how many
  are ticked.

Briefs live outside the repository, so they enter repo lint only through
**CI-safe `Initiative:` reference resolution**. When a workspace root is
discoverable from the repo, an `Initiative: <slug>` line on an epic or a
standalone change must resolve to an existing brief at
`<workspace-root>/initiatives/<slug>/brief.md`, and an unresolvable reference is
an error naming both the workspace root and the expected path. When **no**
workspace is discoverable (a bare CI checkout), the check is skipped silently —
repo lint never depends on files outside the repository. Library and change
lint never walk `initiatives/`; a brief is validated only on demand via
`spec_lint.py --initiative <slug>` (which requires a workspace). The status CLI
carries `initiative-show`, `initiative-sync`, and `initiative-set-status`,
mirroring the epic verbs and likewise requiring a discoverable workspace.

### Wiki — the workspace knowledge store at `wiki/`

The **wiki** is a lint-gated, cross-repo knowledge store living in the workspace
(not any repo) at `<workspace-root>/<content-dir>/wiki/`, beside `initiatives/`
and `projects/`. Every wiki operation resolves the store through workspace
discovery (the nearest ancestor whose `.shipd-config.json` declares `workspace`)
and fails, naming the missing workspace, when none is discoverable. The store
holds:

```
wiki/
  schema.md      the grammar conventions (seeded by wiki-init)
  index.md       the page catalog
  log.md         the append-only activity log
  queue.md       pending questions
  sources/       immutable source material (add-only, never parsed or modified)
  wiki/          the pages, one <slug>.md per page
```

The grammar (binding, enforced by `spec_lint.py --wiki`):

- **Pages.** A page is `wiki/<slug>.md` with a **kebab-case** slug. The slugs
  `index`, `log`, `queue`, `schema`, and `sources` are **reserved** and invalid
  as page slugs. A `[[slug]]` **wikilink** in a page or in `index.md`, outside
  fenced code blocks, must resolve to an existing page.
- **Index.** `index.md` catalogs every page as a line `- [[slug]] — <summary>`
  (lines not matching that entry shape are ignored), and the set of catalog
  entries must **equal** the set of pages under `wiki/` — every page indexed,
  every entry backed by a page (bidirectional coverage).
- **Log.** Every level-2 header in `log.md` matches
  `## [YYYY-MM-DD] <op> | <subject>`.
- **Queue.** `queue.md` holds pending questions as `## q-<slug>` blocks with
  unique kebab-case slugs, each carrying non-empty `- Asked:`, `- Question:`,
  `- Options:`, `- Recommendation:`, and `- Answer:` lines, where `Answer:` is
  `pending` until the user supplies an answer.
- **Sources.** Files under `sources/` are **immutable** — add-only; the engine
  never parses or modifies an existing source, and a staged source overwriting
  an existing one is refused.

Engine verbs (all resolving the workspace, none touching a repo-local path):

- `spec_status.py wiki-init` scaffolds the layout (seeding `schema.md`, an empty
  `index.md`/`queue.md`, a first dated `log.md` entry, and empty `sources/` and
  `wiki/`), refusing when a store already exists.
- `spec_status.py wiki-show` prints the store root, page count, index-coverage
  health, pending-question count, and the last log entry.
- `spec_status.py cat wiki <slug>` prints `wiki/<slug>.md`; the reserved slugs
  `index`, `log`, `queue`, and `schema` resolve to the top-level files.
- `spec_status.py wiki-queue-add <slug> --question … --options …
  --recommendation … [--origin …]` appends a `## q-<slug>` block with a
  current-date `Asked:` line and `Answer: pending`, restoring `queue.md` and
  exiting non-zero on a duplicate slug or an invalid result.
- `spec_emit.py wiki --from <staging-dir>` installs a staged store subset
  (`wiki/<slug>.md` pages, `index.md`, `log.md`, `queue.md`, add-only
  `sources/<file>`): it backs up the affected files, installs the set, runs the
  whole-store wiki lint, and restores the backup byte-for-byte on any finding,
  so an invalid store never lands.

## Epics

An **epic** is the grouping layer of the Initiative → Epic → Change hierarchy: a
feature too large for a single change, decomposed into member changes. It lives
at `.shipd/epics/<slug>/epic.md` and opens with an Introduction stating why the
feature exists, then records the decisions and design the members share, plus
the stub table listing those members. An epic never creates its member changes
— each is born later via `/s:plan`, carrying an `Epic: <slug>` line back to the
epic.

```markdown
# reporting-overhaul
Status: draft
Theme: reliability
Initiative: mvp-readiness

## Introduction

The why first — the problem and its motivation — then the feature in brief and
its intended outcome, with success criteria recommended.

### Non-goals

- What this epic explicitly leaves out of scope.

## Research

- [Payment APIs](../../research/payment-apis/report.md) — optional annotation.

## Video

- [Kickoff call](../../video/kickoff-call/brief.md) — optional annotation.

## Decisions

The cross-cutting decisions every member change inherits.

## Design

The shape of the feature as a whole and the seams the decomposition follows.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| csv-export | Export reports as CSV | low | medium | low | low |
| pdf-export | Export reports as PDF | medium | medium | high | medium |
```

Rules the linter enforces (in library lint and via `spec_lint.py --epic <slug>`):

- **Header.** A `# <slug>` title matching the directory, and a `Status:` line
  whose value is one of `draft`, `ready`, `active`, `complete`. There is **no**
  epic-level `verified` and no epic archival move — an epic stays under
  `.shipd/epics/` with a derived `complete` status.
- **Metadata.** The optional header metadata block recognizes exactly two keys,
  `Theme:` and `Initiative:` (kebab-case values). `Profile:` and `Epic:` are
  **not** valid on an epic (a profile is change-level; epics do not nest), so
  they lint as unrecognized keys. `Theme:` is validated against
  `.shipd-config.json`'s `valid_themes` exactly as on a plan.
- **Sections.** All four of `## Introduction`, `## Decisions`, `## Design`,
  `## Changes` are required, and `## Introduction` must be the **first** level-2
  section — the why-first narrative opens the document ahead of any technical
  content. The Introduction states the problem and motivation (the why) before
  the feature and its intended outcome (the what), with success criteria
  recommended, and closes with a required `### Non-goals` subsection listing the
  scope exclusions.
- **Research (optional).** An epic MAY carry a `## Research` section associating
  research with the epic. `<content-dir>/research/` (default `.shipd/research/`) is
  the reserved home of research artifacts. When the section is present it holds
  at least one markdown list entry `- [title](path)` whose link resolves
  (epic-dir-first, then repo-root) to an existing file under that folder; the
  epic-relative form `../../research/<name>/report.md` is the clickable
  convention. An empty section, a dead link, or a link to a file outside
  `research/` is a lint error. Omit the section entirely when a feature has no
  research — an absent section is exactly as valid as before. The linter never
  walks `research/` on its own; files there are validated only when an epic links
  them.

  A report at `<content-dir>/research/<slug>/report.md` is produced by the
  `/s:research` skill, which searches the question with the session's built-in
  web tools and composes a summary, themed findings, a gaps-and-caveats section,
  and a numbered `## Sources` list. Its **grammar** — enforced by the emit engine
  at install time — is a non-empty `# <title>` on line 1, a `## Sources` section
  with at least one numbered entry (`N. …`), and at least one inline `[n]`
  citation marker; every marker outside fenced code blocks (a `[n](` markdown
  link is not a marker, and code blocks are skipped) must reference a listed
  source number. The report is installed and read back only through the engine —
  `spec_emit.py research <slug> --from <file>` writes it (validate-then-install,
  so an invalid report never lands) and `spec_status.py cat research <slug>`
  reads it.
- **Video (optional).** An epic MAY carry a `## Video` section associating video
  intent briefs with the epic. `<content-dir>/video/` (default `.shipd/video/`)
  is the reserved home of video intent briefs. When the section is present it
  holds at least one markdown list entry `- [title](path)` whose link resolves
  (epic-dir-first, then repo-root) to an existing file under that folder; the
  epic-relative form `../../video/<slug>/brief.md` is the clickable convention.
  An empty section, a dead link, or a link to a file outside `video/` is a lint
  error. Omit the section entirely when a feature has no brief — an absent
  section is exactly as valid as before. The linter never walks `video/` on its
  own; files there are validated only when an epic links them.
- **Stub table.** The `## Changes` section holds a table whose header is exactly
  the six columns `| Change | Description | Code | Integration | Unknowns | Risk |`
  in order, with at least one data row. Each `Change` cell is a kebab-case slug,
  unique within the table; each of the four rating cells (Code, Integration,
  Unknowns, Risk) is one of `low`, `medium`, `high` — the per-change complexity
  estimate.

### Epic status stages

An epic's status is derived from its members, not from a task checklist:

- **`draft`** — authoring in progress; `epic-sync` never touches it.
- **`ready`** — decomposed and approved, but no member started. Promoting to
  `ready` (via `epic-set-status ready`) is refused unless the epic lints clean.
- **`active`** — at least one member has started: a member change is `active`,
  `complete`, or `verified`, or has already merged (archived).
- **`complete`** — every member has merged (archived).

`epic-sync <slug>` re-derives the status from member states: a member is
`archived` when a matching `.shipd/completed/*-<slug>/` exists, else its
`.shipd/planned/<slug>/` plan status, else `unplanned`. All members archived →
`complete`; any member started → `active`; otherwise `ready`. `epic-show <slug>`
prints the epic's status, metadata, and one line per member with its state.

### Membership and slug uniqueness

When a change plan carries `Epic: <slug>`, the linter resolves it: a reference to
a non-existent `.shipd/epics/<slug>/epic.md` is an **error**, while a resolved epic
whose stub table does not list the change's own slug is a **warning** — the
decomposition may legitimately grow, but the drift stays visible.

Member slugs are **repo-unique by convention**. Because the `archived` state is
detected by matching `.shipd/completed/*-<slug>/`, a member slug that collides with
an unrelated archived change of the same name would be read as archived; keep
member slugs distinct across the repository to avoid this.

## Video intent briefs

A **video intent brief** captures what a source recording is meant to convey,
grounded in cited timestamps. It lives at
`<content-dir>/video/<slug>/brief.md` (default `.shipd/video/`), the reserved
home of video briefs — see [On-disk layout](#on-disk-layout).

Its **grammar** — enforced by the emit engine at install time, mirroring the
research report's validate-then-install rule — is:

- A non-empty `# <title>` on line 1, followed by a header metadata block
  carrying a required `Video:` line naming the source recording, plus optional
  `Bundle:` and `Decider:` lines.
- A `## Speakers` section holding at least one `- <name> — <label>` entry.
- An `## Intents` section holding at least one level-3 intent heading, each
  carrying at least one inline `[n]` citation marker.
- A `## Sources` section holding at least one numbered entry (`N. …`) whose
  text opens with a bracketed timestamp (`[HH:MM:SS]`, fractional seconds
  permitted) followed by a speaker name.
- Optional `## Open questions` and `## Gaps & caveats` sections; any other
  unrecognized level-2 section is permitted, not an error.

Citation-marker resolution follows the research report's rule: every `[n]`
marker outside fenced code blocks (a `[n](` markdown link is not a marker,
and code blocks are skipped) must reference a listed source number.

The brief is installed and read back only through the engine —
`spec_emit.py video <slug> --from <file>` writes it (validate-then-install, so
an invalid brief never lands) and `spec_status.py cat video <slug>` reads it.

An epic associates a brief with itself by linking it from the epic's `## Video`
section — see the epic contract's **Video (optional)** rule above.

## Requirement format (master library)

A capability's `spec.md` contains zero or more **requirement blocks**. Each block
is introduced by a level-3 header and carries a stable identifier, a normative
body, and one or more scenarios:

```markdown
### Requirement: Enforce SSO session timeout
id: enforce-sso-timeout

The system SHALL end an SSO session after 30 minutes of inactivity and MUST
require re-authentication before granting further access.

#### Scenario: Idle session is ended
- **WHEN** an SSO session has seen no activity for 30 minutes
- **THEN** the session is invalidated and the next request is redirected to
  re-authenticate
```

Rules:

- **`### Requirement: <title>` header** — a level-3 header opens each requirement
  block. The title is human-readable prose and MAY change freely; it is not the
  merge key.
- **`id:` slug line** — the first non-blank line immediately after the header
  SHALL be `id: <kebab-slug>`. The slug is a kebab-case identifier, unique within
  its capability, and is **immutable across rewording**. It is the merge key: the
  engine matches requirements by `id` only, never by title or body text. Because
  identity lives in the slug, a title or body can be reworded without the merge
  mistaking the edit for an add-plus-remove.
- **Normative body (EARS)** — at least one statement using **SHALL** or **MUST**
  expresses the requirement in EARS style. This is the testable contract.
- **`#### Scenario:` blocks** — each requirement has at least one level-4
  scenario written as GIVEN/WHEN/THEN bullets (`**WHEN**` / `**THEN**`, with an
  optional `**GIVEN**`). Scenarios keep the requirement verifiable.

The content of a requirement — its normalized body plus scenarios, excluding the
`id:` and `base:` metadata lines — is what the engine content-hashes to detect
concurrent edits (see the delta format below).

## EARS notation

EARS (Easy Approach to Requirements Syntax) is the **recommended** shape for a
requirement's SHALL/MUST statements. Five patterns cover the cases:

- **Ubiquitous** (always true): `The <system> SHALL <response>.`
- **Event-driven** (When): `When <trigger>, the <system> SHALL <response>.`
- **State-driven** (While): `While <state>, the <system> SHALL <response>.`
- **Unwanted behavior** (If/Then): `If <undesired condition>, then the <system>
  SHALL <response>.`
- **Optional feature** (Where): `Where <feature is present>, the <system> SHALL
  <response>.`

These templates are authoring guidance, not grammar: the linter enforces only
the presence of a SHALL or MUST token and never rejects a requirement for not
matching an EARS template.

## Delta format (change specs)

A change's `specs/<capability>/spec.md` is a **delta**: it does not restate the
whole capability, only the requirements it adds, edits, removes, or renames. The
merge engine applies it into the master library by exact `id` match.

Intent is expressed with **level-2 operation headers** — these four and no
others:

- `## ADDED Requirements` — brand-new requirements to insert.
- `## MODIFIED Requirements` — existing requirements whose content is replaced.
- `## REMOVED Requirements` — requirements to delete.
- `## RENAMED Requirements` — requirements whose `id` slug changes.

Under each header, requirement blocks use the same `### Requirement:` +
`id:` shape as the master library, plus operation-specific metadata:

- **`base:` line** — every entry under `## MODIFIED Requirements` or
  `## REMOVED Requirements` SHALL carry a `base: <hash>` line holding the content
  hash of the master requirement it was authored against. At merge time the
  engine compares `base:` to the master's current content hash; on a mismatch it
  still applies the change (take-newer) but emits a loud warning, so a stale-base
  overwrite is never silent.
- **`Reason` and `Migration`** — every `## REMOVED Requirements` entry SHALL
  carry both a `Reason:` note (why it is going away) and a `Migration:` note (how
  existing behavior is handled).
- **`FROM:` / `TO:`** — every `## RENAMED Requirements` entry SHALL carry a
  `FROM:` id and a `TO:` id, where `TO:` is a valid kebab-case slug. The engine
  re-keys the master requirement from the old id to the new id.

### Worked example

```markdown
## ADDED Requirements

### Requirement: Rate-limit login attempts
id: rate-limit-login

The system SHALL reject more than five failed login attempts from one IP within
a rolling 60-second window.

#### Scenario: Sixth attempt is rejected
- **WHEN** a client makes a sixth failed login within 60 seconds
- **THEN** the request is refused with a 429 response

## MODIFIED Requirements

### Requirement: Enforce SSO session timeout
id: enforce-sso-timeout
base: a3f9c1

The system SHALL end an SSO session after 15 minutes of inactivity and MUST
require re-authentication before granting further access.

#### Scenario: Idle session is ended
- **WHEN** an SSO session has seen no activity for 15 minutes
- **THEN** the session is invalidated and the next request is redirected to
  re-authenticate

## REMOVED Requirements

### Requirement: Legacy cookie fallback
id: legacy-cookie-fallback
base: 7b21de
Reason: The legacy cookie auth path is no longer supported.
Migration: All clients moved to SSO in the 3.0 release; no action required.

## RENAMED Requirements

- FROM: sso-timeout
  TO: enforce-sso-timeout
```
