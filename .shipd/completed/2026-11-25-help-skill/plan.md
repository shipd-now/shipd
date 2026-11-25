# help-skill
Status: verified
Planned-at: bba3661f3c72eda0e7bfa9854bdc43c91c29ab4b
Gated-hash: 72b5c11bda75

## Idea

Add a read-only `/s:help` skill that answers how-to questions about shipd.

### Motivation

A shipd user with a question such as "How do I handle mid-spec changes?" has no skill to ask. `/s:onboard` is a fixed tour and the docs pages answer no question.

### Details

- Add `plugins/s/skills/help/SKILL.md` and its harness body.
- Add `docs/help.md`, a cheatsheet row, and an `AGENTS.md` mention.
- Add the skill to the read-only roster.

Affected capabilities: `usage-help` (new); `project-readme` and `shipd-interaction` (modified).

### Non-goals

- No change to `/s:ask` or any oracle file. `/s:ask` stays the oracle.
- No online docs and no repository state as sources.
- No website edit; a separate change in `shipd-now-website` can list the new skill.

## Implementation

- **D1. The name is `/s:help`.** No skill, body, doc, or live mention holds it. Rejected: giving `/s:ask` to this skill, which would rename the oracle across about 40 files and move a file that shipd-factory reads by path.
- **D2. The skill reads skills and CLI help only.** It reads each `skills/*/SKILL.md` frontmatter first, then opens only the matching skills and the references they name. It runs `shipd --help` when a CLI verb may answer. It never answers from model memory. The installed plugin has no `docs/`, so skills are the source that matches the installed version. Rejected: fetched docs, which may describe another version.
- **D3. Three honest verdicts.** The answer opens with exactly one of `Supported`, `Partly supported`, `Not supported`. Supported gives numbered steps with exact commands. Partly supported gives the steps, then the gap. Not supported says so and gives the nearest option, or says there is none. Every step names the skill or verb that backs it. The skill runs none of the suggested commands.
- **D4. A decision goes to the oracle.** When the user asks for a project decision, the skill names `/s:ask <decision>` and stops.
- **D5. The skill is read-only,** so it joins `READ_ONLY` in `test_plan_mode_guard_contract.py` and carries no plan-mode clause. It never uses a dialog.
- **D6. Description.** One-liner, shared with the body: "Answer a how-to question about shipd from its own skills — the steps and commands to run, or an honest no." Trigger phrases: "how do I use shipd", "how do I do this in shipd", "shipd help", "/s:help". `/s:onboard` keeps "how does shipd work".

Risk: the model invents a command. The sources rule and the per-step source guard against it.

## Questions and answers

### Q1: What may the help skill read?
- **Question:** What may the help skill read? Options: (1) skills and CLI help; (2) also online docs; (3) also repository state. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Skills, their references, and `shipd --help`.
- **Queued:** q-ask-help-sources

## Readiness attestation

### Problem and motivation

Users cannot ask how to do something with shipd.

Evidence:

- Capability `shipd-onboard`, requirement `onboard-tour-skill`, fixes the tour at nine steps.
- No `plugins/s/skills/help` exists, and a tracked-file search for `s:help` found nothing.

### Scope and non-goals

The change adds one read-only skill and its registrations.

Evidence:

- `plugins/s/skills/ask/SKILL.md:9-18` defines `/s:ask` as the oracle entry; it is not edited.

### Affected capabilities and files

One new capability and two modified ones cover the skill, the cheatsheet rows, and the read-only roster.

Evidence:

- Capabilities: `usage-help`; `project-readme` (`cheatsheet-page-links`); `shipd-interaction` (`harness-plan-mode-guard`).
- Files: `plugins/s/skills/build/tests/test_plan_mode_guard_contract.py:16`, `docs/cheatsheet.md:48`, `AGENTS.md:170`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `plugins/s/bin/shipd --help` exited 0.
- Runnable premise: the suite under `plugins/s/skills/build/tests` ran 3969 tests and ended `OK` at commit bba3661f.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Name: the user asked for `/s:help` in place of reusing `/s:ask`.
- Sources: settled by the user, Q1.
- Registration: settled by `cheatsheet-page-links` and `test_skill_descriptions.py`.
