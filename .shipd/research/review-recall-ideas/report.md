# Raising /s:review recall: ideas from published review systems

> Prepared by the shipd research skill (/s:research).

**Status (9 Oct 2026):** written before the verify stage existed. Idea 2's
verify half has since shipped (0.6.270 on main; step 7 of `/s:review`); its
permissive hunt half and ideas 1, 3 and 4 remain unbuilt. A free check on
existing rounds later found no description suppression in this corpus, so idea
3 stays only as robustness against adversarial descriptions.

## Summary

This report reads the ReviewBench recall report
([reviewbench-recall](../reviewbench-recall/report.md)) and looks for
published techniques that fit its findings. That report found three things.
Repeated rounds catch different findings, so a 3-round union holds 44 golden
findings against 32 per round. 24 golden findings are never caught. In at
least one observed case, Shipd read the file holding three of them and still
didn't report them.

The literature backs four directions. Running several review passes and
merging them raises recall sharply, with diminishing returns past about five
passes [1][2]. Splitting review into a permissive "hunt" stage and a strict
"verify" stage lets the hunt report freely, because a verifier removes false
positives without a measurable recall cost [3][4]. A "find what you missed"
pass raises recall but adds noise unless something filters it [5]. And PR
descriptions that frame a change as safe suppress defect detection [6], which
matters because Shipd reviews with the description in view.

Two cautions apply to the planned criterion dispatch. Structured checklists
improve coverage [7], but elaborate prompts that demand explanations raise
LLM misjudgment rates in code verification [8]. Recall also falls steeply as
a PR's issue count grows [1], so apilix-sized PRs may need splitting rather
than better prompting.

## Repeat and merge: the cheapest recall gain

SWR-Bench ran the same reviewer several times and had an LLM aggregate the
outputs ("Self-Agg"). With Gemini-2.5-Flash at n=10, recall rose 118.83% to
30.44% and F1 rose 43.67% [1]. Returns diminish beyond n=5 while cost scales
linearly. Flash with n=5 beat a single pass of the larger Gemini-2.5-Pro at
lower cost [1].

Cursor's Bugbot used eight parallel passes, each given the diff in a
different random order. It bucketed similar bugs and dropped bugs found by
only one pass [2]. The random order "nudged the model toward different lines
of reasoning" [2].

**Fit for Shipd.** The ReviewBench report measured the ceiling directly: 32
golden findings per round, 44 in the union of three rounds. A 3-pass merge
would target those 12. Bugbot's majority vote trades recall for precision,
so Shipd should take the union and send it through a verifier (next
section).

**Idea 1: multi-pass review with shuffled file order.** Run 2–3 hunt passes
over the same PR, each with the changed files in a different order, then
merge. Long-context models attend best to the start and end of their input
[9]. Shuffling moves each file into a well-attended position in some pass.

**Free check first.** The union of existing 0.6.260 rounds already shows 44.
Precision of that union is unknown, so a full judge of one merged round
would size the noise before any build.

## Hunt, then verify: unblock the reviewer

Bugbot's agentic version hit "the opposite problem: it was too cautious"
[2]. Cursor responded with "aggressive prompts that encouraged the agent to
investigate every suspicious pattern" [2]. That matches Shipd's observed
failure: it read all of `WorkspaceManagerModal.tsx` and reported none of
three defects.

Refute-or-Promote separates generation from adversarial refutation. It killed
about 79% of 171 candidates, 83% in a prospective subset, and the survivors
produced 4 CVEs and accepted standards fixes [3]. A pre-registered ablation
of a verifier stage found that removing it raised findings but cut precision
from 0.471 to 0.353, with no significant recall difference [4]. The verifier
retained 93.8% of true candidates [4]. Lu et al. likewise pair a multi-role
framework for key bug inclusion with a separate filter for false alarms [10].

**Idea 2: split the reviewer.** A hunt stage lists every suspicion per file,
with no severity and no self-censoring. A verify stage, with fresh context,
confirms or kills each one and assigns severity. Refute-or-Promote's
"cold-start reviewers" reduce anchoring [3]. Shipd's sub-agent architecture
already supports a fresh-context verifier.

**Fit with dispatch.** Criterion dispatch makes the hunt exhaustive per file.
The verifier then absorbs the extra noise that dispatch will generate.

## "Find what you missed" passes need a filter

CR-Bench compared a single-shot reviewer with a Reflexion agent that loops on
"discover missed bugs" [5]. Recall rose from 27.01% to 32.76%, but
signal-to-noise fell from 5.11 to 1.95 [5]. The authors call it a
"fundamental design trade-off" [5].

**Implication.** A self-review "what did I miss?" step is worth adding only
behind the verifier from idea 2. On its own it would undo the precision gains
from the 0.6.257 roll-up.

## The PR description can hide defects

A study of confirmation bias in LLM security review found that framing a
change as bug-free cut vulnerability detection by 16–93 percentage points
across four models [6]. Claude 3.5 Haiku fell from 68.4% to 8.5% [6]. The
errors were asymmetric: far more missed defects than extra false alarms [6].
Redacting the description recovered 68.75% of misses in autonomous review,
and an explicit instruction to disregard it restored 93.75% [6].

**Fit for Shipd.** apilix's description claims working features, and the
never-matched defects sit in that feature code. Shipd's description-drift
step needs the description. The defect hunt doesn't.

**Idea 3: hunt blind, compare later.** Run the defect hunt without the PR
description. Feed the description only to the drift step and the verifier.

**Free check (done 9 Oct 2026).** Across 10 rounds without the description
and 18 with it, the per-golden hit rate was 0.340 without and 0.355 with. Six
findings matched only with the description, several reliably; four matched
only without it, each in at most 2 of 10 rounds. The later rounds also ran
newer versions, so the comparison is confounded, but it shows no suppression
in this corpus.

## Criterion dispatch: structure helps, verbosity hurts

Sphinx evaluates reviews by "structured coverage of actionable verification
points" and reports up to 40% better checklist coverage than baselines [7].
That gain comes from training against checklist rewards, not from prompting
alone, so it shows checklists measure coverage well more than it shows a
prompt-time checklist works.

Jin and Chen found that LLMs often misclassify correct code as failing its
requirements [8]. More complex prompts, "especially when leveraging prompt
engineering techniques involving explanations and proposed corrections,"
raised the misjudgment rate [8].

**Design guidance.** Keep each dispatch verdict short: a yes/no or a
location, not a justification. Move explanation to the verify stage. This
matches the ReviewBench report's lesson that mechanical structure moved
recall while wording didn't.

## Large PRs need splitting

In SWR-Bench, recall fell from 38.35% on PRs with one issue to 8.88% on PRs
with five or more [1]. MCR-Bench reports that performance varies widely by
defect type and severity [11].

**Fit for Shipd.** apilix carries most of the never-matched golden findings
and changes 22 files. Shipd already groups files into cohorts (step 1).

**Idea 4: review each cohort in its own pass.** Give each cohort a separate
hunt with its own context, then merge. This applies the position effect [9]
and the issue-count effect [1] together.

## Ranked ideas and cheap tests

| # | Idea | Targets | Evidence | Cheapest test |
|---|---|---|---|---|
| 2 | Hunt/verify split | Never-matched, read-but-unreported defects | [2][3][4] | 3 rounds on apilix; count `WorkspaceManagerModal.tsx` hits |
| 1 | Multi-pass, shuffled order | The ~12 random misses | [1][2][9] | Full-judge one merged 3-round union for precision |
| 4 | Per-cohort passes | Recall collapse on large PRs | [1][9] | apilix only, 3 rounds |
| 3 | Description-blind hunt | Confirmation bias | [6] | Done: no suppression found in this corpus |
| — | Short dispatch verdicts | Dispatch false positives | [7][8] | Fold into the dispatch release |

Ideas 2 and 1 compose: several shuffled hunts feed one verifier. Build the
verifier first, because every other idea adds candidates it must filter.

## Gaps & caveats

- None of the sources benchmark on ReviewBench, so effect sizes won't transfer
  directly. SWR-Bench, CR-Bench and Bugbot each use a different metric.
- Refute-or-Promote and the verifier ablation study security defects, not
  general code review. Both are single-author studies, and the ablation ran in
  lab environments.
- I could not read SWR-Bench's aggregation prompt, so it is unclear whether
  Self-Agg takes the union or votes.
- No fetched source tests severity calibration for review findings. The
  ReviewBench report's own result (concrete examples at the point of rating)
  is the best evidence available.
- The claim that shuffling file order helps rests on Bugbot's report [2] and
  general long-context findings [9], not on a controlled code-review study.
- Cost: multi-pass and hunt/verify both multiply tokens. SWR-Bench reports
  linear cost growth [1]. Shipd would need a budget rule for large PRs.

## Sources

1. Benchmarking and Studying the LLM-based Code Review (SWR-Bench) — https://arxiv.org/html/2509.01494v2
2. Building a better Bugbot (Cursor) — https://cursor.com/blog/building-bugbot
3. Refute-or-Promote: An Adversarial Stage-Gated Multi-Agent Review Methodology for High-Precision LLM-Assisted Defect Discovery — https://arxiv.org/abs/2604.19049
4. The Model Proposes, the Code Disposes: A Pre-Registered Ablation of a Verifier-and-Acceptance Stage — https://arxiv.org/abs/2609.15887
5. CR-Bench: Evaluating the Real-World Utility of AI Code Review Agents — https://arxiv.org/html/2603.11078v1
6. Measuring and Exploiting Confirmation Bias in LLM-Assisted Security Code Review — https://arxiv.org/html/2603.18740v1
7. Sphinx: Benchmarking and Modeling for LLM-Driven Pull Request Review — https://arxiv.org/abs/2601.04252
8. Uncovering Systematic Failures of LLMs in Verifying Code Against Natural Language Specifications — https://arxiv.org/abs/2508.12358
9. Lost in the Middle: How Language Models Use Long Contexts — https://arxiv.org/abs/2307.03172
10. Towards Practical Defect-Focused Automated Code Review — https://arxiv.org/abs/2505.17928
11. From Static to Dynamic: Benchmarking Real-World Code Review with MCR-Bench — https://arxiv.org/abs/2608.27442
