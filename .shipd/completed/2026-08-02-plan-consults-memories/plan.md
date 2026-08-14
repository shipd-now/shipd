# plan-consults-memories
Status: verified

## Idea

Make `/s:plan` proactively read the personal memory store during investigation and apply any relevant captured preference to its plan decisions and output.

### Motivation

Today a personal memory reaches the plan only through the ask-mikk oracle rung, which fires only when an un-inferrable decision would open a user question round — so a memory can never influence the fast path with no open decisions, and an output/style preference (e.g. "prefers ASCII diagrams") never qualifies at all.

### Details

- Add a "consult personal memories" step to the plan Flow: during investigation, read the personal store (`spec_status.py wiki-show --personal`, `cat wiki index --personal`), grep for `memory-*` pages relevant to the change, read the matches, and apply them.
- A relevant memory may shape any plan decision **and** the plan's output/expression (diagram style, tone), not only task-shaping decisions.
- Report each applied memory in visible text with its source slug; a contradicting typed user reply overrides it — same authority as an oracle-settled decision.
- Absent store or no relevant page → skip silently, never block planning.
- The read is direct (no `s:oracle` spawn), so the investigation turn stays oracle-free.

Affected capabilities: `shipd-plan` (modified). Impact: `plugins/s/skills/plan/SKILL.md`, `plugins/s/skills/plan/references/readiness.md`, `plugins/s/.claude-plugin/plugin.json` (version bump); a local plan-eval run. No engine-script or dependency changes.

### Non-goals

- Not changing the `s:oracle` rung or its personal-first resolution order — this adds a complementary direct read, it does not replace or broaden the oracle path.
- Not adding embeddings or a search service — retrieval stays index- and grep-based over markdown, matching `/s:memory`.
- Not touching `/s:build`, `/s:epic`, or any other skill's memory handling.
- Not writing to or mutating the personal store from the plan — the consultation is read-only.

## Implementation

- **Direct index read during investigation**, mirroring how `/s:memory` and `/s:forget` already read the personal store (`spec_status.py --personal`). Rejected: broadening the oracle rung to always spawn an `s:oracle` at plan start — it adds an agent spawn to every plan and strains the "investigation turn stays oracle-free" rule, while a proactive scan for *any* relevant memory is a browse, not a shaped Q&A.
- **Scope covers output/style, not only task decisions** — the driving case ("prefers ASCII diagrams") is an expression preference the oracle rung structurally cannot carry. So the requirement names output and expression (diagram style, tone) explicitly.
- **Reuse the existing visibility/authority contract** — applied memories are reported like oracle-settled decisions (source slug shown, typed user override governs), so the ladder stays coherent: read → memories → ask-mikk → human, user always final.
- **Degrade silently** — `wiki-show --personal` failing (no store) or no relevant page means the step is skipped with no error, exactly as the oracle rung skips an absent personal rung. The consultation never blocks planning.
- **Placement:** the step lives in investigation (the "read" rung), keeping it out of the oracle path; the delta adds one requirement to `shipd-plan` and leaves the existing `oracle-consultation` / oracle-free requirements untouched.

Risk: a stale or over-broad memory silently steering a plan. Guarded by mandatory visible reporting of every applied memory plus the user-override rule, so a wrong application is always surfaced and correctable.
