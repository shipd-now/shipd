# How SWE benchmarks avoid ceiling effects and answer leakage

> Prepared by the shipd research skill (/s:research).

## Summary

Software-engineering benchmarks defend their validity on two fronts, and the
literature treats them as separate problems. **Answer leakage** inflates scores
when the task materials already contain the solution; one audit found that
32.67% of successful patches on SWE-bench simply copied a fix stated in the
issue report or its comments, and removing those instances alongside
weak-test ones dropped a measured resolution rate from 12.47% to 3.97% [1].
**Ceiling effects** destroy discrimination when every arm passes; the saturation
literature defines this as the loss of reliable separating power among top
performers, and treats it as a property of the item set rather than the
grader [2].

The mitigations are mostly curatorial rather than clever. SWE-bench Verified
discarded 68.3% of sampled instances after human annotation, flagging 38.3%
for underspecified problem statements and 61.1% for unit tests that could
unfairly fail a valid solution [3]. Benchmarks that must keep a leaky artifact
instead bound what the agent can reach: one harness benchmark removes commits
after the issue's history boundary, which moved a model from 84.7% to 76.7%
Pass@1 — an 8.0 percentage-point correction attributable to leakage alone [4].

Two findings bear directly on comparing an agent harness against a bare
baseline. First, discriminating power comes from item count, not repeated runs
of one item: repeated seeds reduce only within-question variance and leave
between-question variance untouched [5]. Second, when a task set saturates
against a strong model, the standard remedy is to run the same comparison on a
weaker model, where the harness difference is still visible [4].

## Answer leakage: the contamination inside the task

SWE-bench carries a `hints_text` field defined as the comments made on the
issue before the solution pull request's first commit [6]. That field exists
precisely because those comments frequently state the fix, and it is held
separate from the problem statement the model receives.

Separating the field is not sufficient on its own. A manual audit of instances
that SWE-agent with GPT-4 resolved found 32.67% where the solution appeared
directly in the issue report or comments, and a further 31.08% that passed only
because the tests were too weak to verify correctness [1]. After the authors
removed both categories, the measured resolution rate fell from 12.47% to
3.97% [1] — the reported score had been roughly three times the defensible one.

Where the leaky material cannot be removed, benchmarks bound reachability
instead. Claw-SWE-Bench deletes commits reachable beyond the issue's history
boundary, so an agent can only read and run code that existed when the issue was
filed [4]. That single treatment moved Claude Opus from 84.7% to 76.7% Pass@1,
an 8.0 percentage-point difference [4] — a useful measure of how much a
reachable answer is worth.

## Curation: filtering for solvable, well-specified instances

SWE-bench Verified is the canonical example of curation as the primary defence.
Annotators reviewed 1,699 random samples from the SWE-bench test set to produce
the 500-instance subset [3], which is published as human-validated for
quality [7]. Each criterion carried a severity label from 0 to 3, where 0 and 1
are minor and 2 and 3 mark the sample inadequate [3].

The yield is the striking part. Annotation flagged 38.3% of samples for
underspecified problem statements and 61.1% for unit tests that might unfairly
mark a valid solution incorrect, and 68.3% of samples were filtered out
altogether [3]. Annotators also estimated how long a developer would need to
decide on and implement each solution [3], making difficulty an explicit,
recorded property of the item rather than an emergent surprise.

The grading contract does separate work from the curation. Each instance carries
`FAIL_TO_PASS`, the tests the pull request resolves, and `PASS_TO_PASS`, the
tests that must pass both before and after the patch [6]. The second list is
what catches collateral damage, and it is specified per instance rather than
inferred.

## Saturation: what happens when everything passes

The saturation literature distinguishes stagnation from saturation: stagnation
is statistical indistinguishability among top models, while saturation requires
that indistinguishability **and** top performance approaching the benchmark's
inferred ceiling [2]. A benchmark that no longer separates ability levels is
treated as obsolete regardless of how carefully it grades.

Test-set size is the lever the same work identifies: larger test sets show lower
saturation indices, and the index deliberately downweights raw sample count
through an effective size `n_eff = n^α` with a default `α = 0.5` [2]. Its
recommendations to designers are to report uncertainty-aware statistics and
compression indicators rather than peak scores alone, to use larger test sets
with stratified reporting, and to set explicit retirement criteria once
saturation stays high [2]. Notably, the study reports that private test sets and
open-ended formats do **not** reliably prevent saturation [2] — secrecy is not a
substitute for difficulty.

An item discriminates best when its difficulty sits near the capability being
measured; too easy and frontier systems saturate it, too hard and it separates
nobody [2]. This is the item-response-theory framing, and it implies the
informative band is narrow and must be targeted on purpose.

## Statistical power: breadth beats repetition

Measurement error in an eval decomposes into between-question variance, because
items differ in difficulty, and within-question variance, because the same input
yields different outputs across runs [5]. Averaging three random seeds reduces
the within-question component by a factor of three and leaves the
between-question component untouched [5]. Repeating one item therefore measures
that item's flakiness, not the system's ability.

The sample sizes involved are larger than most suites use. Detecting a
three-point accuracy improvement, from 82% to 85%, requires roughly 2,400
examples per group under a two-proportion z-test at α = 0.05 and 80% power [5].
At 100 examples the minimum detectable effect is nearer 10 to 12 points [5]. The
practical recommendation is 500 to 1,000 diverse, representative examples with
paired analysis, which supports detecting a five-point improvement [5].

## Isolating a harness from the model it runs on

Comparing an agent harness against a bare baseline is a distinct design problem,
and at least one benchmark treats the harness as the controlled variable
explicitly. Claw-SWE-Bench decomposes the stack into a fixed base — prompt
template, task set, execution container, per-instance timeout, patch extraction,
and evaluator — plus a replaceable harness slot [4]. Every harness receives an
identical task-prompt template, the same Docker image with the repository reset
to the instance's base commit, a 3,600-second wall-clock timeout, and the
official evaluator [4]. Patches are extracted from repository state rather than
parsed from the agent's response [4], so a harness cannot win on output
formatting.

Its answer to ceiling effects is the most transferable finding here. The
benchmark runs its sweep on two models — a stronger mid-tier model and a
lower-cost small one — explicitly because ceiling effects may hide harness
differences at high capability, while small-model behavior still exposes
them [4]. Difficulty is balanced rather than sampled: its 80-instance subset
enforces within-language difficulty quartile quotas of 2/3/3/2 to prevent drift
toward easy or hard tasks [4]. That subset preserves cross-harness rankings with
a mean absolute difference of 1.88 percentage points against the full set, and a
maximum of 3.68 [4].

## Gaps & caveats

- **The SWE-agent ablation figure is unverified.** Search surfaces report that
  SWE-agent solves 10.7 percentage points more instances than a plain-shell
  baseline on a 300-instance subset, but the NeurIPS PDF did not yield readable
  text, so the number is recorded here rather than asserted as a finding.
- **SWE-bench Verified's difficulty buckets were not recovered.** The annotation
  asked developers to estimate implementation time [3], but no fetched source
  gave the categorical buckets or their distribution.
- **No source addresses a spec library as the leaky artifact.** The leakage work
  concerns issue comments and future commits. A benchmark whose task materials
  must include a specification the agent is designed to retrieve is not covered;
  the reachability-bounding treatment [4] is the nearest analogue, not a match.
- **The statistical-power figures come from a practitioner blog**, not a
  peer-reviewed source [5]. Its formulas are standard two-proportion power
  calculations, but the specific recommendations are one author's.
- **Pass@k variance was not researched in depth.** Search surfaces indicate
  pass@k is sample-inefficient for ranking, and that Bayesian alternatives are
  proposed, but no source on that was fetched.
- **Publication dates were not verified per source.** Several arXiv entries
  appear recent relative to this report's date; their claims are reported as the
  fetched text states them.

## Sources

1. SWE-Bench+: Enhanced Coding Benchmark for LLMs — https://arxiv.org/abs/2410.06992
2. When AI Benchmarks Plateau: A Systematic Study of Benchmark Saturation — https://arxiv.org/html/2602.16763v1
3. Introducing SWE-bench Verified (OpenAI announcement, mirrored) — https://github.com/irthomasthomas/undecidability/issues/933
4. Claw-SWE-Bench: A Benchmark for Evaluating OpenClaw-style Agent Harnesses on Coding Tasks — https://arxiv.org/html/2606.12344v1
5. Your LLM Eval Is Lying to You: The Statistical Power Problem — https://tianpan.co/blog/2026/04/15/statistical-power-llm-evals
6. SWE-bench Verified dataset card — https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified/blob/main/README.md
7. SWE-bench Verified overview — https://www.swebench.com/verified.html
