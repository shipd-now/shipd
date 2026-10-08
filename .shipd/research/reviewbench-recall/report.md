# Shipd /s:review on ReviewBench: recall across 0.6.247–0.6.266

## Summary

We ran Shipd's `/s:review` locally against five PRs from the ReviewBench test
set (80 valid golden findings), then used the benchmark to test a series of
Shipd changes. Without the PR description, micro grounded recall rose from
28.7% on the 0.6.247 baseline to 35.4% on 0.6.252. With the description, it
rose from 37.1% on 0.6.252 to 40.0% on 0.6.260, and golden findings matched in
at least 2 of 3 rounds rose from 30 to 32. The 28.7% → 40.0% span mixes Shipd
changes with the description, so it is not a measure of either alone.

Mechanical changes moved the numbers, and rewording didn't. Multi-location
findings, the manifest check, the missing-test roll-up and the import-line
location all produced repeatable gains. Rubric rewording stayed within noise,
and two of three severity rewrites failed.

Most misses are systematic. 24 of the 80 golden findings have never matched
in any of 19 five-PR rounds across all versions. Supplying neighbouring files
(`semdiff related`, 0.6.266) did not reach any of them. In one apilix round
the reviewer read all of `WorkspaceManagerModal.tsx` and still reported none
of its three golden defects. The gap is selection, not context.

The scores are unofficial. They come from 5 of the 25 test-set PRs and a
judge that runs through the `claude` CLI. Use them to compare Shipd versions
with each other, not with the public leaderboard.

## Setup

A local runner (`benchy/run-shipd.sh`) checks out each PR's head commit,
removes the remotes, and runs `/s:review <base> <head> --json` in a headless
`claude -p` session. The runner never passes a PR number, because a named PR
makes Shipd post to GitHub. Runs from 0.6.252 onward also pass the PR title
and description (`--pr-context`), as the benchmark mounts them.
`shipd_to_rb.py` writes one ReviewBench finding per entry in `locations`.

ReviewBench's judge normally calls a model API. A `claude-cli` provider in the
local clone calls `claude -p` instead, isolated from local settings, plugins
and MCP servers. A `--grounded-only` flag skips the classifier for unmatched
findings.

| PR | Language | Used for |
|---|---|---|
| k1LoW/gh-copilot-review#9 | Go | All 5-PR rounds |
| brexhq/CrabTrap#15 | Go, TypeScript | All 5-PR rounds, severity tests |
| brianc/node-postgres#3650 | JavaScript | All rounds; pg-pool packaging check |
| cmik/apilix#12 | TypeScript, JavaScript | All 5-PR rounds, context test |
| mheuss/chronicle#14 | Rust | All 5-PR rounds, severity tests |

## Method

- **Grounded recall** is the share of valid golden findings that a Shipd
  finding matched at the same file and lines. Micro recall pools all 80
  findings; macro recall averages per PR.
- **Noise.** Single 5-PR rounds of one version ranged from 29% to 45% recall,
  so one round cannot detect a change smaller than about 10 points. Every
  verdict uses the mean of 3 rounds.
- **Matched in ≥2 of 3 rounds** counts golden findings Shipd catches
  reliably. It resists noise better than the mean.
- **Pre-registered rules.** Before each targeted test, we wrote down what
  counts as a pass. An under-rated issue counted as fixed only if it came out
  medium or higher in most rounds where it appeared.
- **Judge noise** was checked separately. Re-judging the baseline's findings
  gave identical grounded recall. One precision recommendation (treat
  missing-test findings as invalid) failed a re-judge and was withdrawn.
- **Cost.** A 5-PR round costs about 4M review tokens. Judging costs about 5M
  tokens grounded-only, or about 17M with the full classifier.

## Recall by version, all five PRs

| Version | Change | Rounds | Micro recall (range) | Macro recall | ≥2 of 3 |
|---|---|---:|---:|---:|---:|
| 0.6.247 | Baseline | 1×2 | 28.7% | 33.2% | n/a |
| 0.6.249 | Multi-location findings | 3 | 35.0% (30.0–42.5) | 34.6% | 25 |
| 0.6.251 | Low-severity rubric, weak wording | 3 | 33.3% (31.2–36.2) | 32.8% | 26 |
| 0.6.252 | Low-severity rubric, reworded | 3 | 35.4% (27.5–41.2) | 35.9% | 26 |
| 0.6.252 +desc | Same, with PR description | 3 | 37.1% (32.5–40.0) | 38.0% | 30 |
| 0.6.253 +desc | Description drift check | 3 | 36.2% (35.0–38.8) | 40.2% | 27 |
| **0.6.260 +desc** | **Roll-up, manifest check, more** | 3 | **40.0% (40.0–40.0)** | **42.1%** | **32** |

The baseline row is one review run judged twice, so it shows judge noise
only and has no ≥2-of-3 count. Compare "+desc" rows only with each other, because the PR description
changes what the reviewer sees.

## What each change did

| Version | Change | Verdict | Evidence |
|---|---|---|---|
| 0.6.249 | Findings list every location; the first is the fix site | Works | About 4 golden findings recovered in most rounds, all in apilix: `lastSynced`, plaintext credentials, two missing flushes. |
| 0.6.251–252 | Rubric admits low-severity defects; breadth sweep | No effect | About 90 extra low findings over three rounds; recall 35.0% → 35.4%. |
| 0.6.253 | Check the PR description against the diff | Partial | One more golden finding every round, no trivia. The understated-scope case (`WORKSPACES.md:1`) never matched. |
| 0.6.257 | One missing-test finding per group of files | Works | Missing-test findings fell from 42 to 25; other findings held (98 vs 93). |
| 0.6.258 | Package manifest check | Works | Caught the unpublished pg-pool file in 2 of 3 rounds and the apilix lockfile mismatch in 3 of 3. Never rated low. |
| 0.6.260 | Cumulative release | Works | First gain clearly above noise: 40.0% in all three rounds, 32 reliable matches. |
| 0.6.255, 0.6.261 | Severity rules | Failed | Target issues stayed low. 0.6.261 also suppressed edge-case findings (8 → 2). |
| 0.6.262 | Severity, with concrete examples at the point of rating | Works, with a cost | All three targets medium in 3 of 3 rounds. Recall on the test PRs stayed below 0.6.260. |
| 0.6.263 | Allow the import line as a second location | Works | pg-pool finding named `index.js:3` in 3 of 3 rounds on 0.6.266, against 1 of 3 and 0 of 3 before. |
| 0.6.265–266 | `semdiff related` lists neighbouring files | No effect | No starved files after the 0.6.266 fix. Recall flat; no never-matched finding reached. |

## Severity test: chronicle, CrabTrap, node-postgres

Shipd rated three real data-loss or error-hiding defects as low. Each test
ran 3 rounds on these three PRs with the PR description. Cells list the
severity per round; a dash means the issue wasn't reported that round.

| Measure | 0.6.260 | 0.6.261 | 0.6.262 |
|---|---|---|---|
| `move_file` deletes the source on failure | low · – · med | – · – · low | med · med · med |
| `QuerySummaries` hides a database error | low · low · low | low · low · low | med · med · med |
| `cleanup_media` drops rows anyway | med · low · – | med · med · med | med · med · med |
| Edge-case findings, 3 rounds | 8 | 2 | 4 |
| Golden matches per round (of 37) | 11 · 12 · 10 | 11 · 6 · 7 | 9 · 6 · 8 |
| Mean golden matches per round | 11.0 | 8.0 | 7.7 |

The severity fix holds, but recall on these three PRs sits about 3 findings
per round below 0.6.260. Three PRs over three rounds cannot confirm the gap;
a 5-PR, 3-round test on a later version would settle it.

## Where the misses are

| 0.6.260, all five PRs | Golden findings |
|---|---:|
| Matched per round | 32, 32, 32 |
| Matched in at least one of three rounds | 44 |
| Matched at least once by any version | 56 |
| Never matched in 19 rounds | 24 (16 low, 8 medium, 0 high) |

Running each review three times and merging the results would add about 12
findings. The rest stay missed however often the review runs.

17 of the 24 never-matched findings need files beyond the diff. 0.6.266 tested
whether supplying those files helps, with 3 rounds on apilix and node-postgres:

| apilix + node-postgres (47 golden) | 0.6.260 | 0.6.266 |
|---|---:|---:|
| Golden matches per round | 21 · 21 · 23 | 23 · 20 · 23 |
| Mean per round | 21.7 | 22.0 |
| Matched in ≥2 of 3 rounds | 22 | 22 |
| Reachable never-matched findings reached | – | 0 of 5 |
| Reviews that called `related` | – | 3 of 6 |

By the pre-registered rule, the context hypothesis is refuted. Golden labels
name the files a person needs to see a defect. They don't show what Shipd
lacks, because Shipd already reads those files.

## Lessons

- **Change mechanics, not wording.** Every repeatable gain came from a
  structural change: where findings are anchored, a dedicated check, or a
  roll-up step.
- **Put rules where they're applied.** Severity rules in a reference file had
  no effect. The same rule worked at the point of rating, with concrete
  examples. The import-line location followed the same pattern.
- **Watch for suppression.** Tightening the definition of low made some
  findings vanish instead of moving up. Pair any severity change with a count
  of findings by category.
- **Context isn't selection.** The remaining misses sit in files the reviewer
  reads.

## Open work

- **Deterministic criterion dispatch** (in progress). Each changed file gets
  paired with the checks it must answer, and the reviewer gives a verdict per
  pair. `WorkspaceManagerModal.tsx` is the test fixture.
- **Mandatory `related`.** The call joins the first command every review
  runs.
- **Recall gap after the severity fix.** Confirm or rule out the 3-finding
  drop on a full 5-PR, 3-round test.
- **Understated descriptions.** The check for changes a PR description leaves
  out has never fired.
- **Search without ripgrep.** Shipd falls back to `git grep`, which misses
  untracked files. A fix using `git grep --untracked` is queued.

## Reproducing

Tooling lives in `~/projects/benchy`:

- `run-shipd.sh --tag <round> [--pr-context] [--pr <index>]` runs reviews.
- `npm run judge` in `ReviewBench/` with the `claude-cli` provider scores
  them; `--grounded-only` skips the classifier.
- `compare.py NAME=r1,r2,r3 [--show-golden]` compares 3-round configurations.
- `severity_check.py NAME=r1,r2,r3` runs the severity test.
- `tokens.sh <round>` reports token cost.
