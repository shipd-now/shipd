# docs-findings-sweep
Status: verified
Planned-at: d93fff2f383fd537ed902e5a5342d40042a4cebb
Gated-hash: cc39e89c3bf0

## Idea

Fix the findings the reviews and builds of the `docs-by-feature` epic left
open, across the docs pages, four specs, two plugin texts, and one new test.

### Motivation

A reader who follows the docs is told things the engine does not do: a
payload field that does not exist, a merge rule list that looks complete, a
config file the build never creates. Three specs also contradict the pages
they govern, so the next docs change cannot satisfy both.

### Details

Nineteen candidate findings were checked against the repository. All hold at
least in part: half of finding 8 is dropped and finding 12 is narrowed. The
kept fixes, by finding number:

1. `docs/pr.md` — the default merge rules read as a partial list and link
   `customise.md`.
2. `docs/semantic-review-reference.md` and requirement
   `semantic-review-reference-doc` — the finding field is `locations`, an
   array.
3. `docs/semantic-review.md` — `low` is a minor defect, never style.
4. `docs/install.md` — shows the `export PATH=...` line, inline, at 150 lines.
5. `docs/history.md` — link text "Your first change".
6. Stale link text in `docs/guardrails.md`, `docs/room-wake-reference.md`,
   `docs/copilot-review-reference.md`, and four video scripts; video 09 no
   longer calls three doctor lines the last three.
7. `docs/what-is-shipd.md` — the orchestrator runs on the session's model.
8. `docs/cheatsheet.md`, the `shipd --help` banner, and two docstrings in
   `plugins/s/bin/shipd` — "generated command files", no `/s:` label.
9. `docs/statusline-and-telemetry.md` and its requirement — `builds.jsonl`
   sits in `log_dir`.
10. `docs/plan.md` — the gate is the skill's only exit to `ready`; a person
    can also use `/s:status`.
11. `docs/oracle.md` — a wiki page outranks a raw queue entry.
12. `docs/workspaces/external-stores.md` — names the two networked paths
    `store_sync` gates.
13. `docs/room-run.md` and `docs/room-wake-reference.md` — the four dropped
    facts return, in room freed by rewrap.
14. `plugins/s/skills/build/SKILL.md` — the report only reads the config.
15. `plugins/s/bin/shipd` — the docstring stops listing `worktree remove`
    as kept out.
16. Requirement `core-ideas-doc` — the ladder is read, oracle, human.
17. Requirement `install-mode-docs` — permits three README facts (Q1).
18. Requirement `statusline-telemetry-user-docs` — the line ends in `tasks`.
19. A new test guards the root README.

Dropped, with evidence:

- Finding 8, the `docs/harnesses.md` half. `docs/harnesses.md:86` says the
  plugin provides the `/s:` commands to Claude Code. That is true: it
  describes the plugin, not the generated files. `docs/harnesses.md:8` and
  `:99` already say "generated command files".

Narrowed, with evidence:

- Finding 12. The two pages do not contradict each other on the wiki store.
  `store_sync.py` resolves only the wiki store, and the auto-commit itself
  runs no networked git, so both statements hold. The external stores page
  omits two networked paths: `autopilot.py:1165-1175` fetches the store's
  `origin main`, and the hook pushes whatever repository holds the wiki.

Affected capabilities: `project-readme` (three modified, two added),
`shipd-install`, `statusline`, `build-reporting` (one modified each), and
`shipd-cli` (one added). Impact: 19 docs files, `plugins/s/bin/shipd`,
`plugins/s/skills/build/SKILL.md`, three test files, and the plugin version.

### Non-goals

- The engine bug where `shipd statusline layout --config` writes the default
  settings file.
- The old README facts that have no docs page.
- The website repository, and anything under `.shipd/completed/`.
- No edit to `README.md`, `docs/core-ideas.md`, `docs/harnesses.md`, or
  `docs/workspaces/teams.md`: each already states the fact correctly.
- No change to the documentation standard, `docs_lint.py`, or the line caps.

## Implementation

- **Every text change is fixed in advance.** `artefacts/replacements.md`
  holds each old and new text, grouped by file. Each new text was applied to
  a scratch copy and passed `docs_lint.py` inside its cap. The builder
  applies the entries exactly and writes no prose of its own. Rejected:
  describing each fix and letting the builder word it — the caps leave no
  slack on four pages, and wording is judgement.
- **Room comes from rewrap, never from a cut or a new page (Q2).**
  `docs/room-run.md` and `docs/room-wake-reference.md` sit at their caps.
  Reflowing five paragraphs at the pages' own 98-column width frees the
  lines. The run facts go to the reference, because `docs/room-run.md`
  already sends the reader there for the rules; the by-hand flags go to the
  how-to's by-hand step. Result: 149 of 150 and 250 of 250.
- **`docs/install.md` shows the PATH line inline.** A code block costs three
  lines and the page has one. Result: 150 of 150.
- **`docs/plan.md` keeps the skill's rule and adds the person's exit.**
  `shipd-plan` pins the gate as the skill's only exit; `spec-status`
  requirement `status-lifecycle-stages` lets a human transition out. Both
  are true, so the page states both.
- **Finding 8 drops the label instead of naming a prefix.** Generated files
  are `shipd-<command>` on most harnesses but sit under
  `~/.claude/commands/shipd/` on Claude Code, so "generated command files"
  is the one phrase true everywhere. The banner changes with it (Q3).
- **Docs facts with no owning spec statement get two added requirements** in
  `project-readme`, so each task traces to a scenario a validator can
  refute.
- **Tests come first.** `artefacts/test_readme_docs_links.py` is the README
  guard, copied in whole beside `test_config_sample.py`.
  `artefacts/tests.md` holds four methods for `test_shipd_cli.py` and
  `test_build_report.py`; three fail until the plugin texts change.
- **The plugin version goes one above `origin/main`**, read at build time.

Risk: another change edits one of these pages first, and an old text no
longer matches. Each entry's old text occurs exactly once today; a builder
that finds no match stops and reports, and never rewords.

## Questions and answers

### Q1: Which README facts may restate per-repo and dev mode?
- **Question:** `install-mode-docs` says the README restates neither
  per-repo mode nor dev mode, yet the README carries three such facts. Options:
  (1) amend the requirement to permit exactly those three; (2) cut them
  from the README. Recommendation: (1).
- **Answered by:** USER
- **Answer:** Option 1. The repository owner decided, in the brief for this
  change, that the README keeps three facts: the directly runnable vendored
  `.shipd/plugin/s/bin/shipd`, the in-session `/plugin marketplace add
  <path-to-your-checkout>` and `/plugin install s@shipd` steps, and the
  sentence that the plugin is the engine's distribution vehicle for every
  harness. No oracle lookup ran, because the owner had already decided.

### Q2: Where do the four dropped room facts go?
- **Question:** Both room pages are at their caps. Options: (1) rewrap the
  existing pages and add the facts there; (2) a new nested reference page;
  (3) drop the item. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. An over-cap page is not split into a new nested
  reference page, and detail is not cut to fit.
- **Cited:** [[docs-main-page-shape]]

### Q3: Does the banner change with the cheatsheet row?
- **Question:** The cheatsheet's harness row copies the `shipd --help`
  banner's phrase. Options: (1) fix the banner and the docstrings in the
  same change; (2) fix only the cheatsheet row. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1, the planner's recommended default. No person was
  available; the owner's standing instruction for this run was to adopt the
  recommended default on an insufficient verdict. The queue entry stays
  pending for the owner to confirm or overturn.
- **Queued:** q-sweep-help-banner-generated-command-files

## Readiness attestation

### Problem and motivation

The docs state several things the engine does not do, and three specs
contradict the pages they govern.

Evidence:

- `plugins/s/skills/review/scripts/review_gate.py:245` reads `locations`;
  `docs/semantic-review-reference.md:38` documents `location`.
- `plugins/s/skills/build/scripts/build_report.py:1030` is read-only;
  `plugins/s/skills/build/SKILL.md:810` says it creates the config.
- Requirement `core-ideas-doc` names a "memory, oracle, human" ladder;
  `docs/oracle.md:24` says read, oracle, human.

### Scope and non-goals

Nineteen listed findings bound the change; the brief's four exclusions and
four already-correct files stay untouched.

Evidence:

- In scope: the 34 entries of `artefacts/replacements.md`, three test files,
  five delta specs, `plugins/s/.claude-plugin/plugin.json`.
- Out of scope: `docs/harnesses.md:86`, `README.md:111-114` and `:139-140`,
  `docs/core-ideas.md:74`, `docs/workspaces/teams.md:228-229`.

### Affected capabilities and files

Five capabilities and 25 files are affected, because each finding names its
own page or script.

Evidence:

- `project-readme`: `semantic-review-reference-doc` (base 4814d425e4c0),
  `core-ideas-doc` (base d4d0c869fd27), `readme-docs-group-links` (base
  558090463e02); added `docs-sweep-page-facts`,
  `docs-link-text-current-titles`.
- `shipd-install`: `install-mode-docs` (base 960b2216592f). `statusline`:
  `statusline-telemetry-user-docs` (base aa94c163fc10). `build-reporting`:
  `user-configuration-file` (base aa10f1f4482f). `shipd-cli`: added
  `cli-self-description`. Hashes from `spec_status.py base-hash`.
- Runnable premise: `plugins/s/bin/shipd gate rules` → printed
  `approvals: config 2`.
- Runnable premise: `plugins/s/bin/shipd doctor` → printed `fast-pass`,
  `merge-rules`, and `actions-approve` after `copilot-secret`.
- Runnable premise: `plugins/s/bin/shipd --help` → printed `(also: remove,
  prune-branches, hooks)` under `worktree`, and `the generated /s:` under
  `harness`.
- Runnable premise: `docs_lint.py` over a scratch copy of every edited page
  with the entries applied → exit 0; `docs/install.md` 150 lines,
  `docs/room-run.md` 149, `docs/room-wake-reference.md` 250,
  `docs/oracle.md` 242.
- Runnable premise: the README guard and the four new test methods, run in a
  scratch copy → the guard passed; three methods failed before the plugin
  entries and all passed after.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- The three README facts: settled by the user, Q1.
- The home of the room facts: settled by the oracle, Q2.
- The banner's scope: recommended default adopted under the user's standing
  instruction, Q3.
- The README test's place beside `test_config_sample.py`, the phrase for
  finding 8, and the wording of findings 10 and 12: settled by
  investigation.
