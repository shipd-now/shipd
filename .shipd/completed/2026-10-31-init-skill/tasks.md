## 1. Contract test

- [x] 1.1 [req: init-skill-sections, init-constitution-starter, needs-setup-reference, needs-setup-roster] Add
      `plugins/s/skills/build/tests/test_init_skill_contract.py`, modelled on
      `test_plan_deep_skill_contract.py` (same `_read`/`_norm` helpers,
      whitespace-normalized matching). Assert: `plugins/s/skills/init/SKILL.md` has
      `name: init`; `plugins/s/harness/bodies/init.md` line 1 matches
      `<!-- description: .+ -->`; only `init` claims `"/s:init"`; `README.md`,
      `docs/cheatsheet.md`, `AGENTS.md` contain `/s:init`; SKILL.md and body
      name the seven sections, `config set`, `spec_status.py init`,
      `init-status`, `constitution-starter.md`, and `AskUserQuestion` (SKILL.md
      only); `${CLAUDE_PLUGIN_ROOT}/skills/init/references/needs-setup.md` contains `init-status`,
      `--unattended`, `action:`, `none`, `scaffold`, `wizard`, and `/s:init`;
      `${CLAUDE_PLUGIN_ROOT}/skills/init/references/constitution-starter.md` exists and contains `<!--`; for
      each of `plan`, `epic`, `research`, `autopilot`, `status`, `initiative`,
      `build`, both SKILL.md and `harness/bodies/<skill>.md` contain
      `${CLAUDE_PLUGIN_ROOT}/skills/init/references/needs-setup.md`; the normalized texts of those
      fourteen files contain none of `created the first time a change is
      merged`, `stop before searching`, `ask scaffold-or-stop`. Run it and
      observe it fail.

## 2. Reference and starter

- [x] 2.1 [req: needs-setup-reference] Write
      `needs-setup.md` in a new `plugins/s/skills/init/references/` with first line
      `<!-- doc-type: reference -->`, stating the check exactly as
      `plan.md`'s "Needs-setup reference" bullet and the
      `needs-setup-reference` requirement say: the command
      `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py"
      init-status [--unattended]`, run from the root the skill writes into;
      the three `action:` branches; the one printed line on `scaffold`
      (`shipd: created the <content-dir> layout`); the re-check after the
      wizard; the `Error:` stop; the harness plan mode stop. Say every
      content-directory path as "the content directory" (no bare dot-shipd
      literal), so `test_prompt_notation.py` passes.
- [x] 2.2 [req: init-constitution-starter] Write
      `constitution-starter.md` in `plugins/s/skills/init/references/`: a
      `# Constitution` title, a plain paragraph saying the file is optional
      and its rules bind planning and build when present, then the headings
      `## Technology constraints`, `## Testing`, `## Change discipline`, each
      holding only HTML-commented example rules.

## 3. The /s:init skill

- [x] 3.1 [req: init-skill-sections, init-wizard-steps, init-constitution-starter, init-handoff-sections] Write
      `plugins/s/harness/bodies/init.md`: line 1 `<!-- description: Set up
      shipd in a project — a guided first-run wizard, or one section on
      demand — through the engine's init and config verbs. -->`, a
      `# /s:init` heading, `<!-- include:preamble -->`, then numbered steps
      for: `init-status` (stop on unattended after `spec_status.py init`),
      section parsing, the wizard per `artefacts/wizard-keys.md`, set
      detection, `shipd config set` writes and the one re-ask (or, when an
      `error:` line names another key, fixing that key first and retrying
      once), the
      constitution copy (`cp -n`), the hand-off sections, and a closing
      summary listing the on-demand sections. Point at
      `plugins/s/skills/document/references/question-brief.md`. Keep it under the
      `body-content` ceiling.
- [x] 3.2 [req: init-skill-sections, init-wizard-steps, init-constitution-starter, init-handoff-sections] Write
      `plugins/s/skills/init/SKILL.md`: frontmatter `name: init` and a folded
      `description: >-` equal to the body one-liner plus `Trigger phrases:
      "set up shipd", "initialise shipd", "shipd setup wizard", "/s:init".`;
      the version announcement (`shipd:init v<version>`); the `## Harness
      plan mode` section copied from `plugins/s/skills/worktree-hooks/SKILL.md` verbatim; the
      binary resolution; the content-directory path-notation sentence from
      `plugins/s/skills/plan/SKILL.md`; then the same workflow as 3.1 in full, embedding the
      `artefacts/wizard-keys.md` tables, the AskUserQuestion rule (one key per
      dialog, current value first) and the question-brief pointer. Never
      instruct a hand edit of `.shipd-config.json`.

## 4. Route the roster through the reference

- [x] 4.1 [req: missing-layout-guard, needs-setup-roster] In
      `plugins/s/skills/plan/SKILL.md`, replace the `Requirements:` paragraph
      (from "When that layout is missing" through "is safe to re-run.") with
      one sentence: run the needs-setup check in
      `${CLAUDE_PLUGIN_ROOT}/skills/init/references/needs-setup.md` inside the
      change's worktree, right after creating it, before investigating. In
      "What still stops the flow", replace the "Missing content-directory
      layout" bullet with "**First-run setup** — the needs-setup check
      returns `action: wizard`; the `/s:init` wizard runs, then the flow
      continues." In `plugins/s/harness/bodies/plan.md` step 1, replace the "Confirm the
      content directory exists … as though it were there." sentence with one
      naming `${CLAUDE_PLUGIN_ROOT}/skills/init/references/needs-setup.md`, adding no lines.
- [x] 4.2 [req: needs-setup-roster] In `plugins/s/skills/research/SKILL.md`
      replace "**When that layout is missing, stop before searching** … inventing
      a path." with the needs-setup sentence (run in the research worktree);
      in `plugins/s/harness/bodies/research.md` replace the "Confirm the layout
      resolves … invent a path." sentence the same way.
- [x] 4.3 [req: needs-setup-roster] In `plugins/s/skills/epic/SKILL.md`,
      `plugins/s/skills/autopilot/SKILL.md`, `plugins/s/skills/status/SKILL.md`, and `plugins/s/skills/initiative/SKILL.md`
      (for `set` only), append the needs-setup sentence to the
      `Requirements:` paragraph; add one sentence naming
      `${CLAUDE_PLUGIN_ROOT}/skills/init/references/needs-setup.md` to the first numbered step of
      `harness/bodies/{epic,autopilot,status,initiative}.md`.
- [x] 4.4 [req: needs-setup-roster] In `plugins/s/skills/build/SKILL.md`,
      replace "If the layout does not exist yet, it is created the first time
      a change is merged; you never need to run an external init." with the
      needs-setup sentence (run in the change's worktree); add the same
      pointer sentence to step 1 of `plugins/s/harness/bodies/build.md`. Confirm
      `test_init_skill_contract.py` passes.

## 5. Docs and version

- [x] 5.1 [req: init-skill-sections] Add `/s:init` to `README.md`'s skill
      table (after `/s:doctor`), to `docs/cheatsheet.md` (a
      `/s:init [section]` row and `s:init` in the "Spec, build, ship" list),
      and to `AGENTS.md`'s skill sentence ("`/s:init` to set up shipd in a
      project"). In `docs/getting-started.md` section 4 add one sentence: the
      first `/s:plan` in a new repository runs the `/s:init` wizard first, and
      `/s:init <section>` changes one section later. Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py` on the three
      docs files and fix findings.
- [x] 5.2 [req: init-skill-sections] Bump the patch `version` in
      `plugins/s/.claude-plugin/plugin.json` by one over the branch's value.

## 6. Verification

- [x] 6.1 [req: *] Run `python3 -B -m unittest discover -s
      plugins/s/skills/build/tests` and grep the output for `OK` or `FAILED`;
      fix any failure (skill descriptions, question brief, plan-mode guard,
      harness bodies, prompt notation). Run `python3
      plugins/s/skills/build/scripts/spec_lint.py init-skill` clean.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 70 | 28.9k |
| SubagentHandback | 13 | 16.8k |
| Monitor | 21 | 4.3k |
| (no tool) | 0 | 940 |
| Agent | 2 | 800 |
| ToolSearch | 4 | 583 |
| TaskStop | 3 | 232 |
| SendMessage | 1 | 156 |
| **Total** | 114 | 52.7k |
