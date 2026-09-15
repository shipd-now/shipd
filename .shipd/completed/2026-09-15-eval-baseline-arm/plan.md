# eval-baseline-arm
Status: verified

## Idea

Add a no-skill baseline arm to the eval harness, so a behavior-graded case can
be run as an A/B measuring what the skill contributes over a bare agent.

### Motivation

`evals/run.py` can now grade whether the produced software works, but it only
ever runs one arm — a session loaded with the plugin — so a passing case says
the skill works, never that it beats an agent without it.

### Details

- Add `--arm {treatment,baseline,both}` (default `treatment`, today's
  behavior). `baseline` runs sessions with no plugin loaded; `both` runs each
  arm `--runs N` times and reports the two pass rates together.
- Derive the baseline prompt from the case's own `prompt.md` by stripping its
  leading `/s:<skill>` token, so both arms receive identical wording.
- Refuse a baseline arm on a structural case, and refuse a `prompt.md` carrying
  no skill token — both would produce a meaningless comparison.
- Report per-arm pass rates, and gate the exit code on the treatment arm alone.
- Document the A/B in `AGENTS.md`'s `## Evals` section.

Affected capabilities: `skill-evals` (modified). Impact: `evals/run.py`,
`evals/tests/test_runner.py`, `AGENTS.md`. No new dependencies — stdlib only.
Nothing under `plugins/s/` changes, so no plugin version bump.

### Non-goals

- No statistical testing of the two rates; at these run counts a significance
  claim would be noise dressed as rigour. The harness reports rates and stops.
- No new eval case — the A/B runs against `fix-report-drift`.
- No CI wiring for A/B runs; they spawn paid sessions and stay on-demand.
- No change to how either arm is graded — the grader stays arm-neutral.

## Implementation

- **The baseline arm drops `--plugin-dir` and nothing else.** Same fixture,
  same content directory, same `--permission-mode`, same timeout, same grader,
  same resume cap. A controlled experiment varies one thing, so every other
  input is held constant. Rejected: also stripping the fixture's `.shipd/`
  tree — that varies the corpus and the skill together, and then a result
  cannot attribute the difference to either.
- **The baseline prompt is derived, never authored.** `baseline_prompt(text)`
  strips a leading `/s:<skill>` token from the first line and returns the rest
  verbatim. Prompt parity is the experiment's main confound — a hand-authored
  baseline prompt silently sets the result, thin phrasing flattering the skill
  and a full brief flattering the baseline. Deriving makes parity structural.
  Rejected: a sibling `prompt-baseline.md` per case.
- **A prompt with no leading `/s:` token fails the baseline run**, naming the
  case. Both arms would otherwise receive identical input, which measures
  nothing while looking like a result.
- **A structural case refuses a `baseline` or `both` arm**, naming the case.
  Structural grading asserts a change directory, a clean `spec_lint.py`, and
  `Status: ready` — artifacts only the plugin's skills produce, so the baseline
  arm would fail by construction and the comparison would be theatre.
- **The exit code gates on the treatment arm alone.** A baseline arm that fails
  is the expected, informative outcome, not a harness regression; gating on it
  would make a working A/B look like a broken suite. The baseline rate is
  reported and never gates.
- **`Case` gains no arm field.** The arm is a property of the invocation, not
  of the case, so it threads through `execute_case` as a parameter — leaving
  `discover_cases` and `expect.json` untouched.

Risk: a bare agent may still read the fixture's `.shipd/verified/` spec and
solve the case from it, narrowing the measured gap. That is a true result about
this case, not a harness defect — the fixture's spec is part of the repository
both arms are given. Noted so a narrow gap is not misread as a broken arm.
