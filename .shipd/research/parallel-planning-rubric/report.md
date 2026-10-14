# Deciding which epic members can be planned in parallel

> Prepared by the shipd research skill (/s:research).

## Summary

This report asks how shipd should decide which members of an epic can be *planned* (specified) at the same time by independent agents, and whether a hand-authored scoring rubric is the right tool for that call. Today the epic grill plans members strictly one at a time so later planners can read earlier plans. It then runs a cross-plan consistency pass. The autopilot's `--waves` mode already computes *build* waves from capability-directory disjointness, but it computes *plan* waves only from risk chunks.

The evidence points one way. Parallelizability is a property of the *dependency structure* between work items, not of each item in isolation. Engineering practice has a deterministic method for it: the design structure matrix (DSM). A DSM sorts items into sequential, parallel, and coupled relations, then partitions them so coupled cycles collapse into single blocks [1]. Evidence from multi-agent coding shows what an undetected coupling costs. When two agents each get one of a pair of compatible features that touch overlapping code, they succeed about 30% less often than one agent doing both [2]. Concurrent agent PRs from different agents hit textual merge conflicts 41.7% of the time [3]. The dominant failures are duplicated work and divergent architecture, not merge mechanics [2]. Rubric evidence cuts against relying on judgement scores for this decision. Human raters sharing a rubric reached a Krippendorff's alpha of only about 0.1 to 0.2 [6]. LLM judges are self-consistent but drift in severity across model versions [7].

**Recommendation: a hybrid with a deterministic core.** Compute plan waves from a pairwise coupling matrix built from declared, checkable signals: shared interfaces, shared files or capability directories, shared Decisions, data-shape ownership, and ship-order edges. Partition it DSM-style into waves. Use a small rubric only to *declare* the soft signals that cannot be read from the tree, never to produce a summed parallelizability score that decides the waves. Keep the existing consistency pass as the reconciliation step, because hidden coupling is guaranteed to leak through [2][4].

## How engineering methods model parallelizability

A DSM records, for each pair of tasks, whether one needs information from the other. That yields three relations [1]:

- **Parallel:** "Parallel tasks do not interact with each other and can be executed at the same time." [1]
- **Sequential:** one task feeds a later one, so they run in order [1].
- **Coupled:** each task feeds the other, and "any changes in information by either task result in rework." [1]

Steward's partitioning algorithm is deterministic [1]:

1. Place tasks with no inputs first.
2. Place tasks with no outputs last.
3. Find the remaining cycles with depth-first search.
4. Collapse each cycle into a single block.
5. Repeat until stable.

The output is an ordering in which parallel groups fall out as items that share no marks. Coupled cycles become blocks that one agent should plan together, or that must iterate. A secondary heuristic is to keep any unavoidable feedback loops short, so rework is found fast [1].

This maps directly onto shipd's problem:

- Epic members are the DSM's rows and columns.
- A "needs to read the other's plan" edge is the dependency mark.
- A plan wave is a partition level: all members whose inputs come only from earlier waves.
- A coupled block is a set of members that should be planned by one agent, or strictly in sequence.

The same structure is a DAG level schedule once the cycles are collapsed. That is why `--waves` build disjointness and plan waves can share one computation that differs only in its edge predicate.

## What multi-agent coding systems show about coupling

**Coupling is common even when items look separable.** CooperBench pairs features that are compatible but touch overlapping or interdependent code. 77.3% of its tasks have conflicting ground-truth solutions, even though each feature averages only 52.3 changed lines across 1.4 files [2]. Overlap therefore comes from shared code regions, not from large scope [2]. Success fell from 68.6% with two agents to 46.5% with three and 30.0% with four [2].

**Failures are mostly semantic.** CooperBench's failure symptoms were [2]:

- work overlap: 33.2%
- divergent architecture (incompatible design decisions): 29.7%
- repetition: 14.7%
- unresponsiveness: 8.7%

Root causes were mis-modelled expectations of the partner's plan (42%), broken commitments (32%), and communication breakdowns (26%) [2]. Letting the agents talk did not significantly improve success. It nudged naive merge success from 8.64% to 10.71%, but the net effect after conflict resolution was about -0.5 points [2]. The behaviours that did work were all up-front partitioning:

- role division
- resource division (splitting files or line ranges, "which makes conflicts impossible by construction")
- negotiation that converges on one plan before acting [2]

**Concurrency is the norm, and so is conflict.** In 33,596 agent-authored PRs, 40.2% of repositories contained co-active agent PR pairs, and those pairs covered 79.4% of agent PRs [3]. Replayed three-way merges conflicted in 41.7% of cross-agent pairs and 19.8% of intra-agent pairs. 84.4% of the conflicted files were source code, and nearly 42% of the conflicts were structural (modify/delete or add/add) [3].

**Detection signals grade from weak to strong.** Practitioner guidance treats file-level overlap against a common base as "a useful first signal" but noisy, so it is best used as a yellow flag [4]. Hunk-level overlap is stronger, and symbol-level overlap is "often more useful than line overlap" [4]. The same guidance names semantic races that no textual check catches ("Agent A might rename a function while Agent B adds a call site"). It also lists high-risk zones such as schema files, generated clients, lockfiles, and routing tables [4]. It proposes a weighted overlap score (+10 same file, +30 overlapping hunk, +40 rename of a touched symbol) that maps to low, medium, and high labels rather than blocking outright [4]. Worktrees "isolate working directories, not product intent." [4]

**Orchestrators find coupled work hard.** Anthropic reports that multi-agent systems "excel at valuable tasks that involve heavy parallelization." They fit poorly where agents must share context or where there are many dependencies, and coding is the named example [5]. Vague task boundaries made subagents "duplicate work, leave gaps," so each delegated task needs an explicit objective, output format, and boundaries [5].

## Signals that predict independent specifiability

Combining the sources gives five candidate pairwise signals for "member A can be specified without reading member B's plan". The table ranks them by how checkable each one is.

| Signal | Checkable how | Evidence |
|---|---|---|
| Shared files or capability directories | Deterministic: intersect the declared touch-sets | File overlap is a noisy first signal [4]; disjoint partitions make conflicts impossible by construction [2] |
| Shared interface or symbol (one defines, the other consumes) | Semi-deterministic: declared provides/consumes lists | Symbol overlap beats line overlap; renames cause semantic races [4] |
| Shared Decision (both depend on an open epic Decision) | Deterministic if members cite Decision ids | Divergent architecture accounts for 29.7% of failures [2] |
| Data-shape or schema ownership | Declared owner per shape; any non-owner consumer is an edge | Schema files are high-risk collision zones [4] |
| Ship-order constraint | Declared "after" edges | Sequential relation in a DSM [1] |

These are *edges between members*, not attributes of a single member. Per-member ratings such as Code, Integration, Unknowns, and Risk describe how hard a member is. They do not say whether it is independent of a particular sibling. That is why shipd's current risk chunking is a weak predictor of safe plan concurrency. This is an inference from the DSM framing [1], not a measured result.

## Turning signals into waves deterministically

The DSM procedure gives a deterministic path from signals to waves [1]:

1. **Build a member-by-member matrix.** Mark an edge B→A when B consumes something A owns: an interface, a data shape, or a capability directory. Also mark one when A must ship first, or when both cite the same *unresolved* Decision. Two writers of the same file or directory get a symmetric mark, which makes them coupled.
2. **Partition** with Steward's procedure. Members with no inputs form wave 1. Each later wave holds the members whose inputs are all in earlier waves. Cycles collapse into one block, planned by one agent or sequentially within the block [1].
3. **Break ties stably**, for example by stub-table order, so the same epic always yields the same waves.
4. **Grade overlap instead of blocking on it** where a signal is noisy. Shared-directory overlap can widen the consistency pass instead of serializing the members. This mirrors the low, medium, and high labelling of overlap risk [4].

A weighted additive score, like the overlap score in [4], is useful as a *severity* for one edge. It is a poor *decision* rule across edges, because one strong coupling (a rename of a consumed symbol) should dominate any number of absent ones.

## Calibrating a rubric, and its limits

The rubric literature says rubrics can improve reliability when they are analytic and topic-specific and come with exemplars or rater training (Jönsson & Svingby's review of 75 studies, as summarised in [6]). The same review warns that narrowing the format to gain reliability can cost validity [6]. In practice reliability stays low. 28 graders using a shared rubric on 40 programming assignments reached an average Krippendorff's alpha of about 0.2 for correctness and below 0.1 for the softer criteria. No group reached 0.8. The authors conclude that "a shared rubric alone is not enough to ensure consistency." [6]

LLM raters, the realistic rater inside shipd, fare differently [7]:

- Self-consistency was good (phi ≥ .80).
- Correlation with humans fell in a ".47-.56 band."
- Severity spread widely across judges.
- Every model-version contrast shifted severity, by up to 133 points on a 0-1000 scale.

A parallelizability rubric scored by a planner model would inherit the same drift across model upgrades. So if shipd keeps a rubric, it should follow these rules:

- **Score observable facts, not judgements.** Ask "does member B consume a symbol member A defines? yes or no" rather than "how coupled are A and B, from 1 to 5". Binary declared facts avoid the anchor-severity problem [6][7].
- **Calibrate with worked examples.** Keep a fixed set of past epics with known outcomes, such as plans that later needed reconciliation, and check that the rubric's edges reproduce them. Re-check after model upgrades, since severity shifts with version [7].
- **Measure agreement with a chance-corrected statistic** such as Krippendorff's alpha, and do not trust the rubric's edges for gating until agreement clears about 0.67 [6].

## Known failure modes

- **Hidden coupling.** Each agent sees only its own item and misjudges the other's plan. This was the top root cause in CooperBench, at 42% [2]. Declared signals will miss some edges, so a post-hoc consistency pass stays necessary.
- **Interface drift and semantic races.** Text-disjoint changes can still conflict in meaning, as when a rename meets a new call site [4]. Plans in the same wave that both reference an interface owned by a third member can each assume a different shape.
- **Divergent architecture.** Members that each decide the same open question differently account for 29.7% of failures [2]. Any shared *unresolved* Decision should force either sequencing or prior resolution.
- **Reconciliation cost grows with fan-out.** Success drops steeply as more agents work at once [2], and talking does not recover the loss [2]. Wide waves of loosely coupled members can cost more in reconciliation than they save in wall-clock time.
- **Over-decomposition.** Orchestrators that spawn too many subagents or give them vague boundaries duplicate work and leave gaps [5].

## Recommendation

A summed parallelizability *score* is the wrong primary tool. Use a dependency matrix and wave computation, fed by a small declared-signal rubric:

1. Have each epic stub row declare what it **owns** (capability directories, data shapes, interfaces), what it **consumes**, which **Decisions** it depends on, and any **ship-after** edges. This is the rubric, phrased as checkable facts [6][7].
2. Derive the pairwise matrix mechanically and partition it into plan waves with the DSM procedure. Coupled cycles become single-agent blocks [1].
3. Treat file or directory overlap as graded severity that widens review, and treat symbol, schema, and Decision overlap as hard edges [4].
4. Keep the cross-plan consistency pass, now scoped to the edges that crossed a wave boundary or were graded soft. It is the reconciliation step for the hidden coupling the matrix will miss [2][4].
5. Default to sequential planning within a coupled block, and keep waves narrow. Evidence shows coordination cost rises quickly with the number of concurrent agents [2][5].

## Gaps & caveats

- No source measured *planning* (specification) concurrency directly. All of the multi-agent evidence concerns *implementation* by coding agents [2][3]. Transferring it to plan authoring is an inference.
- The socio-technical congruence line of work (Cataldo, Herbsleb, and colleagues) computes coordination requirements from task-assignment and task-dependency matrices. It reportedly links unmet requirements to more failures and lower productivity. Its primary PDFs could not be read in this session, so that support is uncited here.
- The weighted overlap score in [4] is a practitioner heuristic from a vendor blog, not a validated instrument.
- Some thresholds were not independently confirmed. The alpha threshold is stated inconsistently within [6] (0.667 against 0.800). The rubric-structure effect on LLM judge severity, reported in search snippets about [7], was not visible in the fetched abstract.
- No source quantified the wall-clock saving of parallel planning against reconciliation cost. The break-even fan-out for shipd is untested.

## Sources

1. Optimizing processes with a DSM (Kevin Sookocheff) — https://sookocheff.com/post/dsm/optimizing-processes-with-a-dsm/
2. CooperBench: Why Coding Agents Cannot be Your Teammates Yet (arXiv:2601.13295) — https://arxiv.org/html/2601.13295v1
3. AI Agent Pull Requests on GitHub: Frequency, Structure, and Merge Conflict Rates (arXiv:2607.04697) — https://arxiv.org/abs/2607.04697
4. Parallel Worktrees + Clash-Style Conflict Prediction (Grass blog) — https://codeongrass.com/blog/parallel-worktrees-conflict-prediction/
5. How we built our multi-agent research system (Anthropic Engineering) — https://www.anthropic.com/engineering/multi-agent-research-system
6. How Consistent Are Humans When Grading Programming Assignments? (arXiv:2409.12967) — https://arxiv.org/html/2409.12967
7. LLM Judges as Raters: A Pre-Registered Audit of Severity, Halo, Reliability, and Version Instability (arXiv:2608.29517) — https://arxiv.org/abs/2608.29517
