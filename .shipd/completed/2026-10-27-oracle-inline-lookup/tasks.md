## 1. The oracle-lookup verb

- [x] 1.1 [req: oracle-lookup-verb] Add `plugins/s/skills/build/tests/test_oracle_lookup.py`, modelled on `test_wiki_remove.py`'s temp-root and `HOME` fixture, covering every `oracle-lookup-verb` scenario: personal-first with `(personal)` marker, skipped personal rung, nested workspaces giving `(inherited <outer-root>)`, answered queue block as `queue q-<slug>` with the pending block only under the not-evidence heading, `[advisory]` tag, present base store cited `(base)`, verified paragraph cited `verified/<cap> (<req-id>)`, bare-repo fallback store, the no-match `INSUFFICIENT` last line with exit 0, and the 4-per-rung / 6000-character cap with the omitted-count line. Run it and observe it fail.
- [x] 1.2 [req: oracle-lookup-verb] In `plugins/s/skills/build/scripts/spec_status.py`, add paragraph and queue-block unit helpers (split on blank lines; whitespace-collapsed verbatim snippet clipped to 400 characters around the first term hit) and the match rule from plan.md's Implementation ("Matching").
- [x] 1.3 [req: oracle-lookup-verb] In `spec_status.py`, add the wiki rungs: personal pages, then chain stores nearest first (or the fallback store) — pages then answered queue blocks — then the present base store, with citation markers and `[advisory]` tags exactly as plan.md's output format shows. Reuse `_wiki_show_data`, `_resolve_wiki_anchor`, and `sc.workspace_chain`; skip any unresolvable store silently and name it skipped on the header line.
- [x] 1.4 [req: oracle-lookup-verb] In `spec_status.py`, add the spec rung over `verified/*/spec.md` (requirement id from the nearest preceding `id:` line), epic `## Decisions` and `## Design` sections, and `research/*/report.md`, focus project's present repos first, then the invocation root, deduped.
- [x] 1.5 [req: oracle-lookup-verb] In `spec_status.py`, add `cmd_oracle_lookup(root, terms)` printing the header line, the four rung sections, the pending-queue not-evidence section, the cap and omitted-count line, and the `no evidence found — verdict INSUFFICIENT` line; register the `oracle-lookup` subparser with positional `terms` (nargs `+`) beside `search`. Confirm `test_oracle_lookup.py` passes.

## 2. The contract reference and the ask skill

- [x] 2.1 [req: oracle-consultation-contract, compact-question-contract] Write `plugins/s/skills/ask/references/oracle-contract.md` (at most 120 lines): the compact-question shape; running `spec_status.py --root <asking-root> oracle-lookup <2–6 terms>` with one retry on alternative terms when nothing matched; the judging rules (first rung's position-stating snippet, verbatim `Cited:` copied from the snippet's citation, verbatim `Evidence:`, default `INSUFFICIENT`, no model knowledge, topical never suffices); `Authority: advisory` for an `[advisory]` snippet; the duplicate check against the pending list; the queue path (`wiki-queue-add`, `wiki-init` when the store is missing, `Queued: none` naming the missing prerequisites); and the `ANSWER` and `INSUFFICIENT` example blocks carried over from `plugins/s/agents/oracle.md`.
- [x] 2.2 [req: ask-skill, compact-question-contract] Rewrite the consultation steps of `plugins/s/skills/ask/SKILL.md` to read the contract reference, run `oracle-lookup`, judge inline, and on `INSUFFICIENT` queue via `wiki-queue-add` before the AskUserQuestion dialog; remove every `s:oracle` and Agent-tool spawn reference. Keep the capture-rubric steps unchanged.
- [x] 2.3 [req: oracle-consultation-contract] Delete `plugins/s/agents/oracle.md` and `plugins/s/harness/agents/oracle.md`.
- [x] 2.4 [req: oracle-consultation-contract] In `plugins/s/skills/build/tests/test_subagent_contract.py`, delete `OracleChainRungContractTest` and the `ORACLE_CONTRACT` constant, and add a test asserting `oracle-contract.md` exists, is at most 120 lines, names `oracle-lookup`, `INSUFFICIENT`, `Cited:`, `Evidence:`, and `Authority: advisory`, and that neither `oracle.md` agent file exists.

## 3. Plan and autopilot callers

- [x] 3.1 [req: oracle-consultation] In `plugins/s/skills/plan/SKILL.md`'s "The oracle rung" section, the fast-path contract, and the enrichment true-gap step, replace "spawn one `s:oracle` per decision" with one `oracle-lookup` run per decision judged per the contract reference, file each `INSUFFICIENT` with `wiki-queue-add`, and treat a non-zero lookup exit as `INSUFFICIENT`. Remove every `s:oracle` reference except the personal-memory section's "spawns no `s:oracle` agent" sentence, which stays as the verified `memory-consultation` requirement words it.
- [x] 3.2 [req: oracle-aware-driven-sessions, oracle-gate-enrichment, detached-pre-build-drift] In `plugins/s/skills/build/tests/test_autopilot.py`, change the `s:oracle` assertions (goahead reply, build prompt, enrich prompt, replan prompt) to assert `oracle-lookup`, and assert `s:oracle` is absent. In `test_autopilot_skill_contract.py`, assert the skill names `oracle-lookup` and not `s:oracle`. Run them and observe them fail.
- [x] 3.3 [req: oracle-aware-driven-sessions, oracle-gate-enrichment, detached-pre-build-drift] In `plugins/s/skills/build/scripts/autopilot.py`, rewrite `GOAHEAD_REPLY`, the build and enrich stage prompts, and the replan prompt to name `python3 <STATUS_PY> --root <repo> oracle-lookup <terms>` and the contract reference at `<PLUGIN_DIR>/skills/ask/references/oracle-contract.md`, keeping each prompt's ANSWER/INSUFFICIENT fallback wording. Confirm the 3.2 tests pass.
- [x] 3.4 [req: in-session-unattended-prompts] In `plugins/s/skills/autopilot/SKILL.md`, replace the three "spawn agent `s:oracle`" instructions with running `oracle-lookup` judged per the contract reference.
- [x] 3.5 [req: oracle-consultation] In `plugins/s/skills/document/references/harness-plan-mode.md`, replace the `s:oracle` example of a writing agent with filing an oracle miss through `wiki-queue-add`.

## 4. Harness ports

- [x] 4.1 [req: registry-data, registry-agent-source, delegation-agent-ids, agent-rendering] Update `test_harness_registry.py` for `AGENT_ROLES == ("sub-agent", "validator")`, `test_harness_bodies.py` so the `ask` body names no `shipd-oracle` and names `oracle-lookup`, and `test_harness_generate.py` line ~383 to render `opencode`'s `sub-agent`. Run them and observe them fail.
- [x] 4.2 [req: registry-data, registry-agent-source] In `plugins/s/skills/build/scripts/harness_registry.py`, set `AGENT_ROLES = ("sub-agent", "validator")`.
- [x] 4.3 [req: delegation-agent-ids] In `plugins/s/harness/bodies/ask.md`, remove the `if:subagents` `shipd-oracle` delegation and make step 2 run `oracle-lookup` and judge it; update `plugins/s/harness/references/ask.md` to describe the verb-based flow. Confirm the 4.1 tests pass.

## 5. Documentation

- [x] 5.1 [req: agent-surface-docs] In `docs/harness-agents-reference.md` remove the `shipd-oracle` row and in `docs/customise.md` drop `shipd-oracle` from the agent-file list.
- [x] 5.2 [req: oracle-consultation-contract] Rewrite `docs/oracle.md`'s description of how a consultation runs (inline `oracle-lookup` plus the contract, no agent), keeping its mermaid diagram, verdict examples, and capture-loop sections; then run `python3 plugins/s/skills/document/scripts/docs_lint.py docs/oracle.md` and fix findings until it exits 0. Update `README.md`'s `/s:ask` row and the `agents/` tree comment.

## 6. Verification

- [x] 6.1 [req: *] Bump `version` in `plugins/s/.claude-plugin/plugin.json` from `0.6.351` to `0.6.352` (AGENTS.md: every change touching `plugins/s/` bumps the plugin version).
- [x] 6.2 [req: *] Run the full engine suite (`python3 -B -m unittest discover -s plugins/s/skills/build/tests`), grep the output for `OK` or `FAILED`, and run `grep -rn "s:oracle\|shipd-oracle" plugins docs README.md` — the only permitted match is the personal-memory sentence in `plugins/s/skills/plan/SKILL.md`. Run `spec_status.py oracle-lookup pull request base branch` from this repo and confirm the output is under 6000 characters.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 70 | 45.0k |
| SubagentHandback | 2 | 4.0k |
| Monitor | 2 | 739 |
| Read | 2 | 475 |
| (no tool) | 0 | 402 |
| Agent | 1 | 338 |
| **Total** | 77 | 50.9k |
