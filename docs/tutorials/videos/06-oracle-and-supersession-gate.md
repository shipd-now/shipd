<!-- doc-type: how-to -->

# Episode 6: The oracle and the supersession gate

## Introduction

A planner interrupts you for decisions the team already made, and a plan can go stale before anyone builds it. This episode shows the two checks that stop both problems. The oracle answers one compact decision from the wiki before it asks a human. The supersession gate stops a build whose plan newer merges already implement. The episode is for developers who plan changes ahead of building them.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Verification and governance |
| Runtime | 5 minutes |
| Prerequisites | [Episode 2](02-plan-and-specs.md); a workspace with a wiki for the oracle |
| Commands shown | `/s:ask`, `/s:teach`, `/s:build`, `spec_status.py check-base` |

## Script

### 0:00–0:45 The ladder

**On screen:** A three-rung slide reads "read, oracle, human". An arrow marks each rung as costlier than the one below it.

**Narration:** Shipd climbs a ladder before it asks you anything. It reads the codebase and the specs first. The oracle comes next. A human comes last.

### 0:45–2:00 Ask the oracle

**On screen:** The terminal runs `/s:ask should the queue prune answered entries, and after how long?`. The reply opens with `ANSWER`, then shows a `Cited:` line and an `Evidence:` quote.

**Narration:** The oracle takes one compact decision. It searches the wiki and the spec surfaces. When a source states a position, the oracle returns `ANSWER` with a citation and a verbatim quote. It never answers from model knowledge, and it never blocks its caller.

### 2:00–3:00 When nobody has decided

**On screen:** A second `/s:ask` returns `INSUFFICIENT` with a `Queued:` line. A dialog shows the question with the oracle's recommendation listed first.

**Narration:** When no source states a position, the oracle returns `INSUFFICIENT`. It files the question in the wiki queue. The caller then asks you once. A durable answer becomes standing knowledge, so the same question never reaches you twice. The `/s:teach` command later distills the queue into wiki pages.

### 3:00–4:15 The supersession gate

**On screen:** The terminal runs `/s:build` on a planned change. The build stops and lists the finding `id-collision`.

**Narration:** Other pull requests can merge work between `/s:plan` and `/s:build`. When you build a planned change, the build first syncs the branch with main. It then runs the `check-base` verb. A superseded finding stops the build and asks whether to abandon the change or re-scope it. The build runs no execution agent first.

### 4:15–5:00 Read the findings

**On screen:** The terminal runs `spec_status.py check-base my-change`. The output lists `stale-base` and `id-collision` lines, and the exit code shows `4`.

**Narration:** Run the same check yourself at any time. The verb only reads, and it exits `0` when clean and `4` when it finds something. A clean check cannot prove that nothing superseded the plan, so the build still reads the code as a backstop.

## Takeaways

- The oracle returns a cited `ANSWER` or `INSUFFICIENT`, and it never blocks.
- A durable answer you give once becomes standing knowledge in the wiki.
- The supersession gate stops a build whose plan newer merges already implement.

## Next

[Episode 7](07-workspaces-101.md) shows how a workspace holds the wiki that the oracle reads.

## Sources

- [The oracle](../../oracle.md)
- [The supersession gate](../../supersession-gate.md)
