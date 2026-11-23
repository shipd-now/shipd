# ledger-assumption-label
Status: verified

## Idea

Close the low findings the review of `headless-reference` left.

### Motivation

shipd#440 made a headless session record its default as `ASSUMPTION`. The verified `plan-qa-ledger` requirement still says `Answered by` holds only `ORACLE` or `USER`, so the spec library disagrees with the plan skill. The same change left the autopilot constant `ORACLE_JUDGE_NOTE` with no user.

### Details

- The `plan-qa-ledger` requirement names `ASSUMPTION` for a headless default and `PLANNER` for a deferring epic-grill planner.
- `emission.md` says an `ASSUMPTION` entry's answer is the adopted default.
- `autopilot.py` drops `ORACLE_JUDGE_NOTE` and `ORACLE_CONTRACT_PATH`, and the prompt test stops stripping it.

### Non-goals

- No change to any prompt text, the gate or the evals.

## Implementation

- Edit the requirement through a MODIFIED delta, the reference by hand, and remove the two constants.

## Summary

Make the ledger requirement name the `ASSUMPTION` label and remove a dead autopilot constant.
