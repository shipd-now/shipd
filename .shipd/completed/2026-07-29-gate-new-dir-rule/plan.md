# gate-new-dir-rule
Status: verified

## Idea

The context gate's task-path check requires a referenced path to exist or
its parent directory to exist. That flags legitimate new-directory work:
the first autopilot production run was fully rejected on it — both members
parked because their plans created new skill directories
(`plugins/s/skills/research/SKILL.md`) or new test trees, exactly the
shape a new-capability change takes. The rule meant to catch dangling or
typo'd paths is instead vetoing ordinary creation.

This change relaxes the rule by exactly one directory level:

- A task path passes when the path exists, its parent exists, **or its
  grandparent exists** — allowing one new directory of depth, the common
  new-skill / new-test-tree case.
- Paths whose parent *and* grandparent are both missing stay findings —
  deep dangling chains and typos are still caught.

### Non-goals

- No plan-text analysis ("does some task create this dir?") — the check
  stays deterministic and cheap; one level of tolerance covers the
  observed false positives without heuristics.
- No changes to the other three context checks or the gate's exit codes.
- No re-gating of currently parked plans in this change — that is the
  human (or enrichment-flow) step after this merges.

Affected capabilities: `context-gate` (modified). Impact:
`plugins/s/skills/build/scripts/spec_gate.py`,
`plugins/s/skills/build/tests/test_spec_gate.py`, plugin version bump.

## Implementation

- **Grandparent rule.** In the file-reference check, after the existing
  file/parent probes, also accept when
  `os.path.dirname(os.path.dirname(token))` resolves to an existing
  directory inside the repo. Rejected: unlimited ancestor walk — the repo
  root always exists, which would neuter the check entirely; one level is
  the smallest relaxation that passes both observed false positives
  (new skill dir under existing `skills/`, new `tests/` under the root).
- **Finding message** for the still-flagged case updates to name both
  missing levels, so the report reads "neither its parent nor grandparent
  directory exists" — clearer for the enriching human.
- Tests cover: new file in existing dir (passes, unchanged), new file one
  new dir deep (now passes — the `plugins/s/skills/research/SKILL.md`
  shape), two new dirs deep (still a finding), and the reworded message.

Risk: slightly weaker typo detection (a typo'd path one level under an
existing dir now passes); accepted — the build itself fails loudly on a
genuinely wrong path, while a false rejection silently kills an autopilot
run, which is the costlier error.
