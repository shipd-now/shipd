## ADDED Requirements

### Requirement: Build-time teacher agent contract
id: teacher-agent-contract

The plugin SHALL ship the `s:teacher` role contract at
`plugins/s/agents/teacher.md`: a clean-context agent whose spawn message
carries only the change name and the absolute path of the plugin's build
scripts directory, and whose inputs are engine reads only — `cat change
<change>` for the plan's `## Implementation` and `## Questions and answers`,
`wiki-show --json`, `cat wiki index`, `cat wiki schema`, `cat wiki queue`,
candidate pages via `cat wiki <slug>`, and the knowledge capture and capture
durability rubrics — never builder summaries, the orchestrator's conversation,
the code, or the change's delta specs and master requirements. If `wiki-show
--json` fails or reports `present` false or `fallback` true, then the agent
SHALL write nothing and report `skipped — <reason>`. The agent SHALL classify
each candidate — ledger entries answered by USER, implementation decisions
stating a position beyond the change, and answered queue blocks (the ledger's
`Queued:` slugs first, then other answered blocks oldest first) — through the
knowledge capture rubric and, for the Durable tier, the capture durability
rubric: Include SHALL become a page, Consent-gated SHALL be withheld and named
in the report, Exclude SHALL be dropped. A candidate contradicting an existing
page SHALL write nothing and SHALL file a pending block with `wiki-queue-add
--origin "build/<change>"`. The agent SHALL touch at most five pages per run,
updating an existing page over minting a slug, citing `change/<slug>` on every
page, preserving drained answers verbatim in a dated `sources/` file, carrying
`Authority: advisory` for an `advisory: ` answer, and staging `index.md`,
`queue.md`, and `log.md` in full with a `## [YYYY-MM-DD] teach | build <change>`
entry. It SHALL write only through one `spec_emit.py wiki --from <staging>`
call, SHALL never edit store files in place, SHALL never ask a question or run
`wiki-queue-answer`, and SHALL never touch the repository, the change artifacts,
or git. Its report SHALL be one line per outcome — `taught — [[slug]]
(new|updated): <summary>`, `drained — q-<slug>`, `withheld — <item>:
consent-gated`, `queued — q-<slug>: contradiction with [[page]]`, `skipped —
<reason>`, `failed — <reason>`, or the single line `nothing durable` — closed by
a one-line count. The frontmatter SHALL pin no `model:`. The `/s:teach` skill
SHALL name the teacher as the build-time path and itself as the full sweep.

#### Scenario: Contract file carries the flow
- **WHEN** `plugins/s/agents/teacher.md` is inspected
- **THEN** it names `cat change`, `wiki-show --json`, the two rubrics, the
  five-page bound, `spec_emit.py wiki --from` as the only write, the
  `skipped`/`taught`/`drained`/`withheld`/`queued`/`failed`/`nothing durable`
  output lines, and forbids in-place store edits, questions,
  `wiki-queue-answer`, and repository writes, with no `model:` in frontmatter

#### Scenario: Nothing durable writes nothing
- **GIVEN** a change whose ledger holds only oracle-answered entries and whose
  decisions are all change-scoped, and a queue with no answered block
- **WHEN** the teacher runs
- **THEN** no staging emit runs and the report is the single line
  `nothing durable`

#### Scenario: Consent-gated knowledge is withheld
- **WHEN** a ledger answer is a workflow preference the durability rubric
  classes consent-gated
- **THEN** no page or queue block is written for it and the report carries
  `withheld — <item>: consent-gated`

#### Scenario: Answered blocks drain with their standing
- **GIVEN** an answered queue block whose answer begins `advisory: `
- **WHEN** the teacher runs against a workspace store
- **THEN** the distilled page carries `Authority: advisory`, the block is gone
  from `queue.md`, the answer sits verbatim under `sources/`, and the report
  carries `drained — q-<slug>`

#### Scenario: Contradiction is queued, not resolved
- **WHEN** a durable decision contradicts an existing wiki page
- **THEN** neither page is written and `queue.md` gains a pending block whose
  origin is `build/<change>`

#### Scenario: Teach skill points at the teacher
- **WHEN** `plugins/s/skills/teach/SKILL.md` is inspected
- **THEN** it names `s:teacher` as the change-scoped build-time path and keeps
  the sweep as the full path
