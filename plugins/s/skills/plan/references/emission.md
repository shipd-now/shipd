# Emission — authoring the lean artifacts

Once the readiness gate passes (see `readiness.md`), author the change silently.
This is an internal step of planning: there is no separate user-facing spec or
propose skill. You produce the artifacts in a **staging area**, install them
through the engine, and hand off.

**Engine-mediated emission (non-negotiable).** You never write into the spec
tree directly and never construct a storage path from convention. Author the
artifact set in a throwaway **staging directory** (e.g. a `mktemp -d` path),
then install it with the emit engine, which resolves the destination from the
repo's configuration, validates in-process, and — on any lint finding — removes
what it installed and exits non-zero so an invalid change never lands:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py" \
    change <change> --from <staging-dir> --root <repo-root>
```

Run from the repo root (so `--root` may be omitted). If it prints findings and
exits non-zero, fix the staged artifacts and re-run — nothing was installed, so
there is nothing to clean up.

**Format authority:** the on-disk layout and the exact requirement/delta grammar
are defined in the content directory's `README.md` (`.shipd/README.md` under the
default configuration). That file is the source of truth — read it if anything
here is ambiguous. This guide does not restate the grammar; it shows a worked
example and the plan-specific rules for filling each artifact.

**Constitution.** When `.shipd/constitution.md` is present, read it before
emitting and treat its rules as binding constraints on the plan, the delta
specs, and the tasks. Do not author a design or a task that violates it.

**Context economy.** Keep each document lean — `plan.md` and every single delta
spec should stay under ~2,000 tokens (roughly 8,000 characters). The linter
warns above that budget. A document pushing the limit is a signal to decompose
the change, not to write a monolith.

## Pick the change name

Choose a short **kebab-case** slug describing the change, e.g. `dark-mode-toggle`,
`rate-limit-login`, `csv-export`. It becomes the change directory name. Keep it
specific and stable — it is how the change is referenced from here on. The emit
engine refuses an existing destination without `--replace`, so a colliding slug
fails loudly rather than clobbering.

## Staging layout

Author the artifact set inside a throwaway **staging directory** with this shape
(nothing goes into the spec tree until the emit engine installs it):

```
<staging-dir>/
  plan.md
  tasks.md
  specs/
    <capability>/
      spec.md          # one delta per affected capability
  artefacts/            # optional — standalone planning outputs (see below)
    <file>
```

One `specs/<capability>/spec.md` per capability the change touches. `<capability>`
matches an existing master capability when modifying — read the current masters
through the engine, `spec_status.py cat verified <capability>`, rather than by
opening a path — or is a new kebab-case capability name when adding one. Install
the finished staging directory with `spec_emit.py change <change> --from
<staging-dir>` (see the top of this guide).

## plan.md — idea + implementation

A single document holds the whole plan: why and what (the idea) and the binding
technical decisions (the implementation).

**Mandatory header.** Line 1 of `plan.md` MUST be the title `# <change-name>`
— the same kebab-case slug as the change directory — and the first non-blank
line after it MUST be `Status: draft`. Emit `draft`: the change is freshly
authored and not yet approved. (The status advances through the pipeline later
— `ready` at approval, then `active`/`complete`/`verified` during build.) The
linter enforces this header, so a missing or malformed one fails the lint gate.

**Optional header metadata.** When — and only when — the request supplies a
profile, theme, epic, or initiative for the change, emit the matching
`Key: value` line(s) in the header directly under `Status:` (recognized keys:
`Profile`, `Epic`, `Initiative`, `Theme`; every value a kebab-case slug). Honor
the **initiative-through-epic rule**: if the change belongs to an epic, emit
`Epic:` and never `Initiative:` (the initiative is derived through the epic);
emit `Initiative:` only on a standalone change with no epic. Emit `Theme:` only
with a slug the theme vocabulary allows (the resolved configuration's
`valid_themes` — inspect it with `spec_status.py config-show` — when present).
When the request names none of these, write **no** metadata lines — the header
is just the title and `Status:` line, and the change is implicitly `full`
profile. See `.shipd/README.md` for the full metadata grammar.

`Profile: lite` records a lighter-weight change: it permits **brief** `## Idea`
and `## Implementation` sections and makes test-first task ordering optional. It
does **not** drop any artifact — a `lite` change still carries `plan.md`, delta
specs, and `tasks.md`, and every structural lint rule still applies.

**Required sections.** After the header, the document MUST carry a level-2
`## Idea` section followed by a level-2 `## Implementation` section. The linter
errors when either is missing, and when `## Idea` lacks any of the
`### Motivation`, `### Details`, or `### Non-goals` subsections (presence only —
it never checks their order or length). Additional sections MAY follow.

- `## Idea` — fill it in a fixed element order:
  1. **One-sentence summary.** Open with a single sentence naming what the
     change does — the whole Idea in one line, before the subsections.
  2. **`### Motivation`.** A required level-3 subsection of **at most two
     sentences** stating **why** the change is being made — what is wrong or
     missing. It MUST be grounded in the request and repository context, never
     a guess: if you cannot state it precisely from what you have, ask the user
     rather than invent one.
  3. **`### Details`.** A required level-3 subsection stating the concrete
     **what** — the changes (typically a short list) plus the affected
     capabilities and the impact (files/areas touched, dependencies, anything
     transitional).
  4. **`### Non-goals`.** A required level-3 subsection last, listing what is
     explicitly out of scope. At least one exclusion.

  The linter enforces the presence of all three subsections; the order above
  and the length limits are authoring guidance. There is **no Goals section**
  anywhere — not here, not elsewhere. The Idea *is* the goals; stating them
  twice invites drift. The how-level negative space (the approaches you
  considered and dropped) lives in `## Implementation` as per-decision rejected
  alternatives, not in a Goals list here.

- `## Implementation` — where the **judgment** lives: the binding decisions an
  executor must not re-make. When drafting it, look for these decision kinds:
  - **Files and components touched** — the concrete surface the change lands on.
  - **Interfaces and data shapes** — function signatures, schemas, message
    formats, wire/on-disk layouts, when the change introduces or alters them.
  - **Each decision, ADR-style** — the choice made, a short rationale, and the
    rejected alternative where it clarifies why. An executor reading a decision
    should never need to reconstruct why it was made.
  - **Risks and trade-offs** — what could go wrong and how the plan guards it.

  If the change is genuinely trivial, this section may be brief — but it must
  still record why the approach is sound.

  Where an ADR-style decision rests on how an **existing** command, script, or
  flag behaves, that premise falls under the runnable-premise rule in
  `readiness.md`'s Attestation section — verify it by running the command and
  cite the observed invocation and output/exit code, not a pointer to the
  implementation's source. See `readiness.md` for the full rule and its
  exemptions.

```markdown
# dark-mode-toggle
Status: draft

## Idea

Add a persisted light/dark theme toggle to the settings panel.

### Motivation

The system only renders in a light theme; users on OLED displays report eye
strain at night and have asked for a dark theme, and there is no way to switch.

### Details

- Add a theme toggle control to the settings panel.
- Persist the choice and apply it on load.

Affected capabilities: `ui-theming` (modified). Impact: `src/ui/settings.py`,
`src/ui/theme.py`; no new dependencies.

### Non-goals

- No automatic theme following the OS appearance — a manual toggle only.
- No per-component theming or custom palettes beyond light/dark.

## Implementation

- Persist the theme in the existing settings store rather than a new file, so
  it rides the current migration path. Rejected: a dedicated theme file — extra
  I/O for one enum value.
- Store the value as a `theme` enum (`light` | `dark`) on the settings schema;
  apply it at first paint to avoid a light-to-dark flash.

Risk: a stale persisted value from a future theme name; guard by falling back
to `light` on an unknown value.
```

### `## Questions and answers` — the oracle ledger

When one or more ask-mikk oracle consultations ran while planning the change,
`plan.md` carries an optional `## Questions and answers` section after the two
required ones. It is the durable record of those consultations: one entry per
consultation, in consultation order, so each settled decision keeps a stable
`Q<n>` reference the user can correct later with `/s:teach <change> Q<n>`.

**No consultations, no section.** A planning session that never consulted the
oracle emits no `## Questions and answers` section at all — an empty or
placeholder section is wrong.

**Record every consultation**, not just the ones the oracle settled. An
`ANSWER` entry carries the oracle's position and its cited sources; an
`INSUFFICIENT` entry carries the user's typed resolution and the `q-<slug>` the
oracle filed in the wiki queue, which is what later lets `/s:teach` drain that
queue entry.

Each entry is a `### Q<n>: <one-line question summary>` header — numbered
sequentially from `Q1` — followed by a dash list of fields:

- `- **Question:**` the full compact question as it was put to the oracle
  (decision, options, recommendation).
- `- **Verdict:**` `ANSWER` or `INSUFFICIENT`.
- `- **Answered by:**` `ORACLE` or `USER`, directly above the answer so who
  settled the decision is clear at a glance.
- `- **Answer:**` the oracle's position in full for an `ANSWER` entry, the
  user's typed resolution for an `INSUFFICIENT` one.
- `- **Cited:**` the oracle's sources — on `ANSWER` entries.
- `- **Queued:**` the filed `q-<slug>` — on `INSUFFICIENT` entries.

The linter errors on a present section that holds no entries, on a header that
is not `### Q<n>: <summary>`, on numbering that does not run sequentially from
`Q1`, and on an entry missing its `**Question:**`, `**Answered by:**`, or
`**Answer:**` field.

**Phrasing rule — stay clear of the gate's marker scans.** The
context-sufficiency gate scans *all* of `plan.md` outside its own
`## Context insufficient` section, so a ledger entry must never contain a
placeholder marker (`TBD`, `TODO`, `FIXME`, `XXX`, the two-word phrase the gate
matches for an unresolved question, or a bare `???`). Paraphrase the
consultation into settled prose; never paste a transcript that still carries
those markers. Trim to the decision, the options, and the answer — the plan's
~8,000-character budget covers this section too.

```markdown
## Questions and answers

### Q1: Which store holds the toggle?
- **Question:** Should the persisted theme live in the existing settings store
  or a dedicated theme file? Options: (1) settings store; (2) theme file.
  Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** The settings store — option 1. It already persists user-scoped
  display preferences and rides the current migration path, so a dedicated
  file would add I/O for one enum value without a second reader.
- **Cited:** verified/ui-theming, wiki/settings-store

### Q2: What does the toggle default to on first run?
- **Question:** Should a fresh install default to `light` or follow the OS
  appearance on first paint? Options: (1) always `light`; (2) read the OS
  appearance once. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Default to `light` — following the OS appearance is explicitly a
  non-goal for this change, and a fixed default keeps first paint deterministic.
- **Queued:** q-theme-default
```

## Delta specs — the contract

Each `specs/<capability>/spec.md` is a **delta**, not a full capability restate.
Use only the four operation headers (`## ADDED`, `## MODIFIED`, `## REMOVED`,
`## RENAMED Requirements`) — see `.shipd/README.md` for the full grammar. Every
requirement block needs an `id:` slug, at least one **SHALL**/**MUST** statement,
and at least one `#### Scenario:` (exactly four hashtags).

**Phrase SHALL/MUST statements in EARS.** The five EARS patterns — ubiquitous
("The system SHALL ..."), event-driven ("When <trigger>, the system SHALL ..."),
state-driven ("While <state>, the system SHALL ..."), unwanted-behavior
("If <condition>, then the system SHALL ..."), and optional-feature
("Where <feature>, the system SHALL ...") — are the recommended shape for
normative statements; see `.shipd/README.md` for the templates. This is
authoring guidance, not a lint rule: the linter requires only a SHALL/MUST
token, never a matching template.

### Worked example — `specs/reporting/spec.md`

```markdown
## ADDED Requirements

### Requirement: Export report as CSV
id: export-report-csv

The system SHALL provide a `--csv` flag on the `report` command that writes the
report rows as RFC 4180 CSV to stdout, and SHALL exit non-zero if the report is
empty.

#### Scenario: CSV flag emits rows
- **WHEN** a user runs `report --csv` on a non-empty report
- **THEN** the rows are written to stdout as comma-separated values with a header
  line

#### Scenario: Empty report is an error
- **WHEN** a user runs `report --csv` and the report has no rows
- **THEN** the command writes nothing and exits with a non-zero status
```

### `base:` hashes for MODIFIED / REMOVED

Every entry under `## MODIFIED Requirements` or `## REMOVED Requirements` needs a
`base: <hash>` line — the content hash of the master requirement you are editing
against. Read the current master through the engine (`cat verified`, never by
opening a path) and hash the requirement:

```bash
S="${CLAUDE_PLUGIN_ROOT}/skills/build/scripts"
python3 "$S/spec_status.py" cat verified "$CAP" | python3 - "$CAP" "$ID" <<'PY'
import sys
sys.path.insert(0, __import__("os").environ["CLAUDE_PLUGIN_ROOT"] +
                  "/skills/build/scripts")
import spec_common as sc
cap, rid = sys.argv[1], sys.argv[2]
# `cat verified` prints a `--- <relpath>` separator first; drop it before parse.
text = "".join(l for l in sys.stdin if not l.startswith("--- "))
for r in sc.parse_spec(text).requirements:
    if r.id == rid:
        print(sc.content_hash(r))
PY
```

REMOVED entries additionally need a `Reason:` and a `Migration:` line; RENAMED
entries need `FROM:` and a kebab-case `TO:`. See `.shipd/README.md` for these.

### Design scratch reference (when a design exists)

This is **presence-based**, never an active prompt: only follow it when a
design (mockups, comps, a spec) was parked for this change in its scratch
directory — resolve or create it with
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/design.py" path
<change-name>`, which prints the absolute `<designs-root>/<change-name>` path
(default `~/.shipd/designs/<change-name>`, overridable via the resolved
configuration's `build.design_dir`). When a design exists there:

- Name it by **absolute path** in `plan.md`'s `## Implementation` section, as
  one of the binding decisions, e.g.:
  ```markdown
  - Design reference: `/home/mikk/.shipd/designs/dark-mode-toggle/` — read
    verbatim by the execution sub-agent and the validator as a read-only,
    out-of-worktree reference; match it, never edit it.
  ```
  The design travels by that plan-named path, never as prose pasted into a
  spawn message — the artifacts stay the compiled source of context.
- Author the observable properties the implementation must match against that
  design as ordinary `#### Scenario:` blocks in the change's delta specs —
  same grammar as any other scenario — so the validator refutes them by
  exercising the real behavior against the design. A refuted fidelity
  scenario blocks `verified` exactly like any other refuted scenario.

When a change carries no design, name nothing and add no design-fidelity
scenarios — every other emission convention is unchanged.

### Artefacts — standalone planning outputs (when one exists)

This is also **presence-based**: only follow it when planning drafts a
standalone output that must be preserved exactly — a policy document, a block
of verbatim text, anything the lean artifact set would otherwise have to
paraphrase. Stage it under the staging directory's `artefacts/` subdirectory
rather than pasting it into `plan.md`, `tasks.md`, or a delta spec, and
reference it by its change-relative path (`artefacts/<file>`) from every
artifact that depends on it: `plan.md`'s `## Implementation` where it informs a
binding decision, `tasks.md` where a task must apply it, or a delta spec where
a requirement is stated in its terms. Stage nothing the change references
nowhere — the emit engine refuses an artefact no artifact names. When planning
produces no such output, stage no `artefacts/` directory and emission is
unchanged.

## tasks.md — the implementation checklist

A flat markdown checklist of `- [ ]` items, grouped under `##` headings, ordered
so they can be executed top to bottom. These are consumed by lower-tier
execution agents, so write them accordingly (see the discipline below).

### Worked example — `tasks.md`

```markdown
## 1. CSV export

- [ ] 1.1 [req: export-report-csv] Add `tests/test_report_csv.py` covering a
      non-empty report (rows + header) and an empty report (no output, non-zero
      exit). Run it and observe it fail — the `--csv` flag does not exist yet.
- [ ] 1.2 [req: export-report-csv] Add a `--csv` boolean flag to the `report`
      command parser in `src/cli/report.py`.
- [ ] 1.3 [req: export-report-csv] In `src/cli/report.py`, when `--csv` is set,
      write rows via the stdlib `csv` module to stdout with a header line.
- [ ] 1.4 [req: export-report-csv] In `src/cli/report.py`, exit non-zero when the
      report has no rows under `--csv`; confirm `tests/test_report_csv.py` now
      passes.
```

### Task discipline (mandatory)

Tasks are executed by a lower-tier agent that does **no architectural thinking**
— it follows the spec and the plan you wrote. Write every task to that standard:

- **Small and single-purpose.** One concrete change per task; if a task hides two
  changes, split it.
- **Independently executable and ordered.** A task can be picked up and finished
  on its own; where order matters, sequence the list so top-to-bottom works.
- **Names its target file(s)/area.** Every task points at the concrete file or
  location it changes (e.g. `src/cli/report.py`), never "somewhere in the CLI."
- **Judgment-free.** No task may require a decision. Every "which approach?",
  "what should the interface be?", or trade-off belongs in the `## Implementation`
  section and the delta specs — resolved *before* emission — not left in the
  executor's head. If a task would force the executor to choose, the plan wasn't
  ready; resolve it and rewrite the task as a mechanical instruction.
- **Test-first ordering.** Where a task has a testable surface, sequence the
  failing-test task *before* the implementation task that makes it pass — the
  test encodes the contract the implementation then satisfies. Docs-only or
  otherwise untestable tasks are exempt; do not invent a test where there is no
  runtime surface to observe.
- **Traceability tag (mandatory).** Every task MUST carry exactly one
  `[req: ...]` tag naming the delta requirement id(s) it implements or verifies:
  `[req: <id>[, <id>...]]` for the ids the task satisfies, or the lone wildcard
  `[req: *]` for a whole-change task such as a verification barrier (the wildcard
  never combines with ids). The ids MUST resolve against the requirement `id:`
  slugs declared in this change's own delta specs — no master-library ids, no
  ids from other changes. Place the tag in the task text after the optional
  `[P<n>]` parallel-group tag; it does not affect task coordination. The linter
  errors on a task with no tag, more than one tag, a wildcard mixed with ids, or
  an id that does not resolve.
