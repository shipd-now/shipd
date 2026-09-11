# shipd-document

### Requirement: One canonical standard file
id: document-standard

The shipd documentation standard SHALL live in exactly one file,
`plugins/s/skills/document/references/standard.md`, structured as three
sections: `## Core rules` — active voice only; descriptive sentences of at
most 25 words; procedural sentences of at most 20 words; one text category
(description or instruction) per sentence; paragraphs of at most 6
sentences; specific verbs over vague "make"/"do"/"take"; noun clusters of at
most 3 words — `## Documentation rules` (the doc-type marker, line caps,
mermaid policy, and a shipd glossary in which each domain term has exactly
one defined meaning), and `## Voice digest` (a self-contained distillation
of the core rules for conversational output, at most 12 lines). `SKILL.md`
SHALL direct the reader to that file by path and SHALL NOT restate the
rules; it SHALL drive the flow: classify the doc, write or rewrite to the
standard, run the lint, and fix findings until the lint exits 0. The skill
SHALL only edit documentation files — it SHALL NOT commit, push, or open a
pull request.

#### Scenario: The standard file carries the three sections
- **WHEN** `plugins/s/skills/document/references/standard.md` is read
- **THEN** it contains `## Core rules`, `## Documentation rules`, and
  `## Voice digest`, with every rule above in its section and the glossary
  defined once

#### Scenario: The skill references, never restates
- **WHEN** `plugins/s/skills/document/SKILL.md` is read
- **THEN** it names `references/standard.md` as the rules source, contains
  no second copy of the numeric rule caps, and instructs running
  `scripts/docs_lint.py` until clean

#### Scenario: An invocation ships nothing
- **WHEN** an `/s:document` invocation completes
- **THEN** no commit, push, or pull request has been created by the skill
  itself

### Requirement: Config-gated voice digest at session start
id: document-voice-hook

The plugin's `hooks.json` SHALL register a `SessionStart` hook running
`scripts/voice_digest.py` (stdlib-only). When the layered configuration's
`voice` key resolves true — the default when absent — the script SHALL print
the `## Voice digest` section body of `standard.md` to stdout and exit 0.
If `voice` resolves false, or the standard file is missing or lacks the
section, or configuration resolution fails, then the script SHALL print
nothing and SHALL still exit 0.

#### Scenario: Default injects the digest
- **WHEN** `voice_digest.py` runs with no `voice` key declared in any
  configuration layer
- **THEN** it prints the voice digest body and exits 0

#### Scenario: voice false silences the hook
- **WHEN** `voice_digest.py` runs where the resolved configuration declares
  `voice: false`
- **THEN** it prints nothing and exits 0

#### Scenario: A broken environment never breaks session start
- **WHEN** `voice_digest.py` runs with `standard.md` absent
- **THEN** it prints nothing and exits 0

### Requirement: Doc types with hard length caps
id: document-length-caps

The standard SHALL require every conforming doc to open with a first-line
marker `<!-- doc-type: concept -->`, `<!-- doc-type: how-to -->`, or
`<!-- doc-type: reference -->`, and SHALL cap total file lines at 100 for
concept, 150 for how-to, and 250 for reference. The lint SHALL report a
missing or unknown marker as an error and an over-cap file as an error.

#### Scenario: Over-cap concept doc fails the lint
- **WHEN** `docs_lint.py` runs on a file whose first line declares
  `doc-type: concept` and which has more than 100 lines
- **THEN** it prints an error naming the cap and exits 1

#### Scenario: Missing marker fails the lint
- **WHEN** `docs_lint.py` runs on a markdown file with no first-line
  `doc-type` marker
- **THEN** it prints an error asking for the marker and exits 1

### Requirement: Diagram policy — the structural test
id: document-diagram-policy

The standard SHALL allow a mermaid diagram only when it carries structure
prose cannot: three or more interacting components, a lifecycle with
branches, or a topology. The standard SHALL cap diagrams at one per doc and
SHALL forbid a diagram that restates an adjacent list or table. The lint
SHALL report more than one mermaid fence in a doc as an error.

#### Scenario: Second mermaid fence fails the lint
- **WHEN** `docs_lint.py` runs on a doc containing two ```mermaid fences
- **THEN** it prints an error citing the one-diagram cap and exits 1

#### Scenario: One justified diagram passes
- **WHEN** `docs_lint.py` runs on an otherwise-conforming doc with exactly
  one mermaid fence
- **THEN** no diagram-count finding is reported

### Requirement: Stdlib-only lint over the checkable rules
id: document-lint-cli

`plugins/s/skills/document/scripts/docs_lint.py` SHALL be stdlib-only Python 3
and SHALL check, over prose outside code fences: sentence word caps (20 words
inside numbered-list items, 25 elsewhere), paragraphs over 6 sentences, the
doc-type marker and its line cap, and the mermaid-fence count — each as an
error. It SHALL report passive-voice matches as warnings that never affect
the exit code. If a sentence boundary follows a known abbreviation (e.g.,
i.e., etc., vs.) or falls inside an inline-code span, then the linter SHALL
NOT split the sentence there. Findings SHALL print as
`file:line: error|warning: message`; the exit code SHALL be 0 with no
errors, 1 with any error, and 2 on usage or unreadable-file problems.

#### Scenario: Long descriptive sentence is an error
- **WHEN** a doc paragraph contains a 30-word sentence outside any numbered
  list
- **THEN** the lint prints a `file:line: error:` finding naming the 25-word
  cap and exits 1

#### Scenario: Long procedural sentence uses the tighter cap
- **WHEN** a numbered-list item contains a 22-word sentence
- **THEN** the lint reports an error naming the 20-word procedural cap

#### Scenario: Passive voice is warning-only
- **WHEN** a doc's only finding is a passive-voice match
- **THEN** the lint prints a `warning:` line and exits 0

#### Scenario: Clean doc exits 0
- **WHEN** the lint runs on a conforming doc
- **THEN** it prints nothing (or only warnings) and exits 0

### Requirement: Skill registration surfaces
id: document-registration

The plugin SHALL register the skill on its standard surfaces: an
`/s:document` row in the repo `README.md` skill table, an `AGENTS.md` rule
that documentation under `docs/` is authored and revised through
`/s:document` plus a mention in its skill list, a CI `unittest discover`
line for `plugins/s/skills/document/tests`, a harness body template at
`plugins/s/harness/bodies/document.md` opening with a
`<!-- description: ... -->` marker (per the harness-command-bodies
capability), and a plugin version bump in
`plugins/s/.claude-plugin/plugin.json`.

#### Scenario: The surfaces name the skill
- **WHEN** the change is merged
- **THEN** `README.md`'s skill table has an `/s:document` row, `AGENTS.md`
  names `/s:document` for docs authoring, `ci.yml` discovers the skill's
  tests, and the plugin version is bumped

### Requirement: Full-scope docs lint in CI
id: docs-ci-marker-gate

The repository's CI workflow (`.github/workflows/ci.yml`) SHALL carry a step
that selects every markdown file under `docs/` (recursive), excluding
`docs/retros/`, and runs
`plugins/s/skills/document/scripts/docs_lint.py` over the selected files —
with no marker-based filtering, so a file without a first-line doc-type
marker is selected and fails through the lint's own missing-marker error. If
a selected file produces a lint error, then the step SHALL fail with a
non-zero exit. When no file qualifies, the step SHALL print a skip notice
and pass without invoking the lint.

#### Scenario: Unmarked doc fails the workflow step
- **WHEN** the step's `run:` body executes against a `docs/` tree holding a
  markdown file with no first-line doc-type marker
- **THEN** the step exits non-zero and the output names the missing marker

#### Scenario: Marker doc with an error fails the workflow step
- **WHEN** the step's `run:` body executes against a `docs/` tree holding a
  file whose first line is a doc-type marker and whose content violates the
  standard (e.g. an unknown type or an over-cap file)
- **THEN** the step exits non-zero

#### Scenario: Clean tree passes
- **WHEN** the step's `run:` body executes against a `docs/` tree whose every
  non-retro file conforms to the standard, marker included
- **THEN** the step exits 0

#### Scenario: Retros are exempt
- **WHEN** the step's `run:` body executes against a tree whose only markdown
  file sits under `docs/retros/` and would fail the lint
- **THEN** the file is not selected and the step exits 0

#### Scenario: Empty docs tree is a pass
- **WHEN** the step's `run:` body executes against a tree whose `docs/`
  directory holds no markdown file outside `docs/retros/`
- **THEN** the step prints a skip notice and exits 0 without running the lint
