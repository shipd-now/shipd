# oracle-naming-sweep

Status: verified

## Idea

Retire the legacy "mikk"/"ask-mikk"/"automikk" persona vocabulary and the
"CodeRabbit" product mention from every live surface, replacing them with
"the oracle" and "popular code-review tools" phrasing.

### Motivation

Live skills, agents, docs, tests, and verified specs still speak of the
"ask-mikk oracle", "mikk's standing opinion", and a "CodeRabbit-style" review,
and `verified/project-readme` still carries the stale requirement id
`readme-displays-the-auto-mikk-banner`. The user asked for zero references to
this legacy naming: the middle rung is simply "the oracle", and third-party
review tools are described generically.

### Details

- Rename "ask-mikk oracle" → "the oracle", the "read → ask-mikk → human"
  ladder → "read → oracle → human", "mikk's standing opinion/answer" → "the
  user's standing opinion/answer", and "teach mikk" → "teach the oracle"
  across `plugins/s` (skills, agent, harness bodies, `autopilot.py` prompt
  strings), `docs/`, `README.md`, `AGENTS.md`, and `.shipd/README.md`.
- Replace "CodeRabbit-style" with popular-code-review-tools phrasing in
  `plugins/s/skills/review/SKILL.md` and the README's `/s:review` row.
- Neutralize test fixtures: speaker "Mikk" → "Ada", `/home/mikk` →
  `/home/user`, origin `teach-mikk` → `teach-session`, with assertions
  updated in lockstep.
- Sweep the wording of `verified/shipd-ask` and `verified/epic-autopilot`
  directly, and rename `project-readme`'s stale requirement id via a RENAMED
  delta.

Affected capabilities: `project-readme` (modified via a RENAMED delta);
`shipd-ask`, `epic-autopilot`, and `shipd-duck` receive direct wording fixes
per the am-naming-residue Q1 precedent (`shipd-duck` — plus the duck skill
and harness body — shipped after planning and surfaced via the residual
scan, whose mandate is to fix any non-allowlisted survivor). Impact: ~10 `plugins/s` skill/agent/harness
files, `autopilot.py`, five test modules, `docs/oracle.md`,
`docs/cheatsheet.md`, `README.md`, `AGENTS.md`, `.shipd/README.md`, plugin
version bump.

### Non-goals

- No edits under `.shipd/completed/` — archives are immutable (constitution).
- No edits to `.shipd/epics/` or `docs/retros/` — historical records (Q1);
  the `epic/mikk-knowledge` citation pinned by `verified/shipd-teach` and
  quoted in `plugins/s/skills/teach/SKILL.md` stays, since it names that kept
  epic.
- No edits to `tools/port.py`/`tools/tests/test_port.py` (the automikk→shipd
  mapping is the tool's function, mandated by `verified/shipd-port`) and no
  edits to the `~/.automikk/` legacy-home negative guards in
  `build_report.py`, its tests, or their spec (Q2).
- No edits to author-name fields ("Mikkel Bergmann") or
  `mikkelbergmann`/`mikkel-bergmann` account and path tokens — a person's
  name, not the persona.
- No renaming of functional identifiers that never carried the persona:
  skill names (`/s:ask`, `/s:teach`), the `s:oracle` agent id, store paths
  (`~/.shipd-memory`), and queue/page slugs are already neutral.

## Implementation

- **Replacement vocabulary (from the request).** "ask-mikk oracle" → "the
  oracle" (docs title "# The oracle"); ladder "read → oracle → human";
  "mikk's standing X" → "the user's standing X" (the oracle serves the
  user's captured knowledge); "teach mikk" → "teach the oracle"; trigger
  phrases "ask mikk"/"consult mikk"/"teach mikk" → oracle equivalents;
  "CodeRabbit-style, AST-aware semantic review" → "AST-aware semantic review
  in the style of popular code-review tools". Rejected: a new proper noun —
  the agent is already named `s:oracle`, so "the oracle" is the existing
  identity.
- **Cross-references renamed in lockstep.** `plan/SKILL.md`'s section header
  "The ask-mikk rung" becomes "The oracle rung"; `references/readiness.md`
  and `references/dialogue.md` name that header verbatim and are updated in
  the same task, so no dangling section reference survives.
- **Master-sweep mechanism (per the am-naming-residue Q1 precedent).**
  Direct boundary-anchored rewrites in `verified/shipd-ask` and
  `verified/epic-autopilot` — wording only, no id, behavior, or scenario
  change — gated by the library lint and the residual scan. The delta-owned
  `verified/project-readme` is excluded from the direct sweep; its stale id
  is retired by this change's RENAMED delta
  (`readme-displays-the-auto-mikk-banner` →
  `readme-displays-the-shipd-banner`), applied by `spec_merge.py` at merge
  (grammar per `spec_lint.py` and the lean-format-drift worked example).
- **Fixture renames.** Speaker "Mikk — product lead" → "Ada — product lead"
  and `[..] Mikk:` transcript lines → `Ada:` in `test_spec_lint.py`,
  `test_spec_status.py`, `test_spec_emit.py`; `- Asked: 2026-07-30
  teach-mikk` → `teach-session` in `test_spec_common.py`,
  `test_spec_lint.py`, `test_spec_status.py` (including the `--origin`
  round-trip); `/home/mikk` → `/home/user` in `test_tui_bootstrap.py` and
  `references/emission.md`'s design-path example. Assertions that quote
  these strings are updated in the same edit.
- **Residual scan (the completion gate).** After the sweep:
  `grep -rniE "mikk|coderabbit" plugins/s docs README.md AGENTS.md tools
  install.sh action.yml .shipd/verified .shipd/README.md evals
  --exclude-dir=__pycache__` must return only: `tools/port.py` +
  `tools/tests/test_port.py` automikk mapping tokens; the `~/.automikk/`
  negative guards in `build_report.py` + `test_build_report.py`; the
  `epic/mikk-knowledge` citation in `verified/shipd-teach` and
  `plugins/s/skills/teach/SKILL.md`; and "Mikkel Bergmann" /
  `mikkelbergmann` / `mikkel-bergmann` author, account, and path tokens.
  Any other survivor is a failure to fix, not a warning.
- **Version bump.** Read main's current
  `plugins/s/.claude-plugin/plugin.json` version at build time (0.6.154 at
  planning) and bump one patch — derived, not hardcoded, since main moves.
- **Runnable premises verified.** The scans above ran this session and
  enumerated every hit; `python3 -m unittest discover -s
  plugins/s/skills/build/tests` → `Ran 1956 tests … OK` this session; the
  RENAMED grammar is validated in-process by `spec_emit.py` at install.

Risk: a swept prose string some test asserts verbatim (prompt strings in
`autopilot.py`, fixture assertions) — bounded by updating fixtures and
assertions in the same task and re-running the full build and review suites;
the residual scan lists its allowed survivors explicitly so nothing is waved
through silently.

## Questions and answers

### Q1: Are epics and retros swept or kept as history?

- **Question:** Should the sweep also edit `.shipd/epics/` (including the
  epic directory named `mikk-knowledge`, cited by `verified/shipd-teach`) and
  `docs/retros/`, or leave them untouched as historical records? Options:
  (a) leave untouched, like `.shipd/completed/` — recommended; (b) sweep
  prose but keep names; (c) full sweep including the epic rename.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a). The am-naming-residue precedent scoped its sweep to
  live surfaces and left epics as history; `verified/shipd-teach`'s scenario
  normatively pins `epic/mikk-knowledge` as its example, so renaming the
  directory or rewriting the citation would break a verified scenario. The
  only retro hit is a `mikkel-bergmann` account URL — a name, not the
  persona.
- **Cited:** completed/2026-08-17-am-naming-residue, verified/shipd-teach,
  .shipd/constitution.md

### Q2: What happens to the functional automikk tokens?

- **Question:** Two live surfaces carry functional automikk tokens: the
  `tools/port.py` mapping table (+ tests) and the `~/.automikk/` legacy-home
  negative guards in `build_report.py` (+ tests). Options: (a) keep both as
  documented exemptions — recommended; (b) delete the port tool and retire
  the guards; (c) keep the tool, retire the guards.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a). The am-naming-residue residual scan already
  adjudicated the build-report tokens as required survivors — guards must
  name the paths they forbid — and the port tool is mandated by the live
  `verified/shipd-port` capability, so deleting it is spec drift, a separate
  product decision. Both exemptions must be listed explicitly in this
  change's residual-scan allowlist, not waved through silently.
- **Cited:** completed/2026-08-17-am-naming-residue/plan.md,
  verified/shipd-port
