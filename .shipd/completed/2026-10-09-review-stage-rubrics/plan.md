# review-stage-rubrics
Status: verified
Theme: reliability

## Idea

### Motivation

Nine rounds of measurement say v0.6.260 beats v0.6.271 on both axes. On all four
benchmark PRs, recall per round went 26.7 to 24.3 and grounded precision 0.439
to 0.393. On chronicle, CrabTrap and node-postgres, matches per round ran
11/12/10 at v0.6.260 against 7/6/8 at v0.6.271, with the three-round union
collapsing 17 to 8. Eight of nine later rounds sit below v0.6.260's worst round.

The losses are **pre-verifier**. Six findings matched under v0.6.260 and are now
gone: `toggleExpanded`, `AuditTrail.tsx:105`, `files.rs:1`, `client.js:722`,
`client.js:12`, `index.js:218`. So the severity rubric line costs recall, and
the verifier is not where it is lost.

The suspected mechanism is the `low` definition. v0.6.261 replaced v0.6.260's
wording with "a real defect whose impact is contained: nothing lost, corrupted,
exposed, or promised and unmet" — four negations a reviewer must satisfy before
rating anything low. Edge-case findings collapsed 8 to 2 on that change.
v0.6.262's no-drop rule recovered them only to 4. The concrete instances fixed
*rating*; nothing fixed *reporting*.

### Details

benchy-cf's proposal, which dominates the straight revert my user first chose:
**the two stages get two different rubrics.** The hunt gets v0.6.260's
reporting wording back. The strict rubric with its concrete instances survives
where rating now happens — in the verifier.

That keeps v0.6.260's recall and v0.6.271's severity, rather than trading one
for the other. A straight revert would give back the three data-loss defects
being rated `medium`, which a user cares about even though recall cannot see it.

### Non-goals

- **v0.6.263's further-location rule is not touched.** It postdates v0.6.260 and
  is the one fix that reached 3 of 3 reliably — the pg-pool import line. A
  careless revert would drop it.
- No change to the verdict shape, the payload, the caps, `semdiff`, or severity
  ownership. The verifier still decides.
- No change to the breadth sweep or the risk lenses.

## Implementation

### Two rubrics, named apart

The crux the proposal does not state: the spawn currently quotes "the rating
step it has just read", meaning `SKILL.md` step 8. If step 8 becomes
v0.6.260's wording, the verifier loses the concrete instances that fixed
severity — the split needs two rubrics, not one relocated.

So they separate by job and by name:

- **Step 8 is the reporting rubric.** What counts as a finding worth reporting,
  and a provisional severity. It carries v0.6.260's `low` verbatim: "a real but
  minor defect: swallowed errors, resource leaks on rare paths, dead or
  duplicated code, unread variables, unstable ids, or blocking calls in async
  contexts. Pure style, naming, and formatting are never findings." No
  containment test, no four negations.
- **`references/verification.md` carries the rating rubric.** v0.6.272's strict
  wording — the impact rule with its three concrete instances, and the
  contained-impact `low` — because that is where severity is now decided.

The spawn quotes the **rating** rubric from `verification.md`, not step 8.

**This does not violate v0.6.271's no-second-copy rule.** That rule forbids two
copies of the *same* rubric drifting apart. These are two different rubrics for
two different stages: one says what to report, the other says how to rate. The
test pinning the absence of a copy must be re-aimed accordingly, not deleted.

### Why kinds under `low` are safe again

v0.6.260's `low` lists defect kinds, and v0.6.262 measured that listing them
caused serious defects to be rated low. That is no longer the hunt's problem: it
proposes, and the verifier overrides with the strict rubric in hand. The listing
is now a *detection aid at the reporting stage* rather than a severity class at
the rating stage, which is what the kinds were always better suited to be.

### The exposure floor appears in both, deliberately

The degradation path keeps every finding's proposed severity when the verifier
does not run. So if the exposure floor lived only in the rating rubric, a
credential exposure or an unchecked authorization boundary could ship at `low`
on any review whose spawn was denied — and that path now fires in the wild, as
the withheld-`Agent` check confirmed.

So the exposure floor sits in both rubrics. Not duplication for its own sake:
the absolute has to hold on whichever rubric ends up final.

### Blind verification, and the drift exception

The spawn message SHALL NOT carry the pull request's title, description or any
summary of it. benchy-cf traced the CrabTrap kill to a leak in the spawn text —
the composing session wrote the description in, and the verifier killed a valid
golden finding reasoning "the PR description states total is returned via
Count, so the extra COUNT is the intended cost". That is confirmation bias
arriving at the rating stage.

**A `description-drift` candidate cannot be judged blind**, and a single blind
verifier would kill every one on principle — which it did, at index 4 of round
c. So drift candidates are verified in a **separate spawn that carries the
description and only the description**, never the diff-blind defect spawn.

### Discovery order

The candidate list is in **discovery order** — the order the passes produced
candidates — stated explicitly rather than left to "deterministic". Severity
order would correlate position with proposed severity and permanently confound
anchoring with merit, which is the question the `candidate` field exists to
answer and currently cannot.

### Surfaces

`plugins/s/harness/bodies/review.md` carries both rubrics inline, since it can
read no reference. Its worst case is 194 of 250, so there is room.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.272 → 0.6.273.

## Readiness attestation

### Problem and motivation

The severity rubric costs recall at the reporting stage, and the fix that
earned severity parity only needs to apply at the rating stage.

Evidence: nine rounds measured by benchy-cf. All four PRs, recall 26.7 to 24.3
and precision 0.439 to 0.393 against v0.6.260. Three PRs, matches per round
11/12/10 at v0.6.260 against 7/6/8 at v0.6.271, union 17 to 8. Six named
findings matched under v0.6.260 and lost since, all pre-verifier. Edge-case
counts 8 to 2 to 4 across v0.6.260, v0.6.261 and v0.6.262. Round c of CrabTrap
killed a valid golden finding citing the PR description, from session
fdfdbe4c, with the description present in the spawn text and no description
fetch in the verifier's tool calls.

### Scope and non-goals

In scope: the reporting rubric on `SKILL.md` step 8 and the harness body, the
rating rubric in `references/verification.md` and the harness body, the spawn
quoting the rating rubric, the exposure floor in both, the description ban, the
drift spawn, discovery order, tests, the version bump.

Out of scope: v0.6.263's further-location rule, the verdict shape, the payload,
the caps, `semdiff`, severity ownership, the breadth sweep, the risk lenses.

### Affected capabilities and files

One capability, one requirement.

Evidence: `semantic-review` requirement `review-skill`, base `229e8f86377a`,
computed with `spec_status.py base-hash` in this worktree. Files:
`plugins/s/skills/review/SKILL.md`,
`plugins/s/skills/review/references/verification.md`,
`plugins/s/skills/review/references/json-output.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/harness/references/review.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: `SKILL.md` is 377 lines against a 400 ceiling;
the worst rendered harness body is 194 against 250; v0.6.260's `low` and impact
floor were recovered verbatim from commit `e360273`; `verification.md` line 93
keeps proposed severities when the verifier is skipped, which is why the
exposure floor must appear in the reporting rubric too.

### No open task-shaping decision

- One rubric relocated or two rubrics: two, because the spawn quotes step 8 and
  moving step 8's text would strip the verifier of the instances that fixed
  severity — settled above.
- Whether two rubrics breach the no-second-copy rule: no, that rule forbids two
  copies of one rubric; these are two rubrics with different jobs, and the test
  is re-aimed rather than deleted — settled above.
- Where the exposure floor lives: both, because the degradation path makes the
  reporting rubric final and that path fires in the wild — settled above.
- What happens to drift candidates under a blind verifier: a separate spawn
  carrying only the description — settled above, and the constraint was
  benchy-cf's.
- Which order the candidate list takes: discovery order — settled above.
