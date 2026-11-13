# PR analysis — last 50 closed PRs (#368–#417)

## Headline stats

- Merged: 50/50
- Median time open → merged: 0.2 h (p90 1.2 h)
- Median size: +390 / -16 lines, 8 files
- Clean first pass (no review findings, no CI failure): 27/50
- PRs with review findings: 23/50
- PRs the review gate blocked (❌ Fix required at least once): 9/50
- PRs with a CI failure: 2/50 (3 failed of 84 CI runs)
- Final review verdict ✅ Ship it on every merged PR

## Review findings

- Unique findings: 45 (posted as 60 threads; repeats come from 'also recurs at')
- Severity: high 3, medium 10, low 32
- Test-gap findings ('No test …'): 7
- Outcome:
  - fixed silently (file changed later, no reply): 25 (56%)
  - fixed (replied): 14 (31%)
  - declined with reason: 6 (13%)
- Fix rate (fixed ÷ all): 87%; high+medium fix rate: 100%

### Outcome by severity

| severity | fixed (replied) | fixed silently | declined | unclear | ignored |
|---|---|---|---|---|---|
| high | 0 | 3 | 0 | 0 | 0 |
| medium | 5 | 5 | 0 | 0 | 0 |
| low | 9 | 17 | 6 | 0 | 0 |

### Findings by area

- skill:build: 11
- docs: 9
- skill:room: 8
- skill:review: 6
- plugins/s: 4
- .shipd/epics: 2
- .shipd/completed: 2
- skill:init: 1
- .shipd/planned: 1
- skill:epic: 1

### Findings by PR kind

| kind | PRs | PRs with findings | findings | gate blocked | CI failed |
|---|---|---|---|---|---|
| docs | 11 | 4 | 7 | 1 | 0 |
| epic bookkeeping | 7 | 2 | 2 | 0 | 0 |
| feature | 29 | 16 | 35 | 8 | 1 |
| fix | 1 | 1 | 1 | 0 | 1 |
| research | 2 | 0 | 0 | 0 | 0 |

### Size vs findings

- 0–100 lines changed: 9 PRs, 1 with findings, 0.1 findings/PR
- 100–500 lines changed: 19 PRs, 10 with findings, 0.7 findings/PR
- 500–1000 lines changed: 13 PRs, 6 with findings, 0.8 findings/PR
- 1000–∞ lines changed: 9 PRs, 6 with findings, 2.2 findings/PR

## High and medium findings

- #408 **high** [fixed silently (file changed later, no reply)] The wrapper applies the sandbox config without validating it, so an absolute or parent-escaping env path points a state variable outside the sandbox.
- #396 **high** [fixed silently (file changed later, no reply)] The production judge_fn accepts model= but the drift step calls it with effort=, so the real seam raises TypeError before its turn runs
- #378 **high** [fixed silently (file changed later, no reply)] The heartbeat thread can overwrite the poster's done claim commit with a beat, so the claim is then released and the head is reviewed again.
- #416 **medium** [fixed (replied)] The teacher stages the full index.md, queue.md and log.md from an earlier read, with no guard against a concurrent writer to the same workspace store.
- #413 **medium** [fixed (replied)] Only untouched-caller and spec-coverage findings stay counted outside the hunks, so a contract or test-coverage finding placed at its fix site in unchanged code
- #407 **medium** [fixed (replied)] The plugin version 0.6.361 is no longer above main: #408 (e5f8a2b) already shipped 0.6.361 on main.
- #404 **medium** [fixed (replied)] The change is marked complete but never archived: it stays under .shipd/planned/ and its requirement is not merged into .shipd/verified/
- #398 **medium** [fixed silently (file changed later, no reply)] config-set and config-unset still run the schema-compat gate, so an invalid `dir` value blocks the very verbs the writer's hint names as the fix
- #388 **medium** [fixed (replied)] The PR body's /context evidence gives the Skills category total but not the per-skill rows the change moved, which the context-budget epic Decision requires.
- #378 **medium** [fixed silently (file changed later, no reply)] The poster never checks that the claimed head is the head it posts on, so a push during a turn lets a review and success status land on an unclaimed head.
- #378 **medium** [fixed silently (file changed later, no reply)] The claim is marked done only when a review object was submitted, so a post that writes the summary but submits no review leaves the head released and room-revi
- #378 **medium** [fixed silently (file changed later, no reply)] Every reviewer turn is claimed per head, so after a head is reviewed (claim done), later question or status tasks to that reviewer on the same head are silently
- #378 **medium** [fixed silently (file changed later, no reply)] The claim gate treats any task another agent opened as a review request, so a question or status task the author opens to the reviewer after the review is done 

## Per-PR table

| PR | kind | +/- | commits | findings | gate ❌ | CI ❌ | hours | title |
|---|---|---|---|---|---|---|---|---|
| #417 | feature | +781/-34 | 1 | 0 | 0 | 0 | 0.2 | ☕ Read After dependencies from the spec store's repository |
| #416 | feature | +1565/-64 | 2 | 1 | 1 | 0 | 0.5 | ☕ Teach the workspace wiki after every verified build |
| #415 | feature | +426/-97 | 2 | 0 | 0 | 0 | 0.3 | ☕ Autopilot delivers every member without asking |
| #414 | docs | +654/-161 | 6 | 0 | 0 | 0 | 0.2 | ☕ Scrub the host codename and add the factory setup page |
| #413 | feature | +1612/-63 | 2 | 3 | 1 | 0 | 1.0 | ☕ Low and already-there findings never request changes |
| #412 | feature | +6/-6 | 2 | 0 | 0 | 0 | 0.2 | ☕ statusline labels the task counter "tasks" |
| #411 | docs | +247/-130 | 2 | 0 | 0 | 0 | 10.1 | ☕ Rename the public App page to shipd-factory |
| #410 | feature | +604/-117 | 1 | 1 | 0 | 0 | 0.1 | ☕ Show one settings sheet in /s:init instead of nine dialogs |
| #409 | fix | +247/-15 | 3 | 1 | 0 | 1 | 0.4 | ☕ Fix sandbox-run symlinked homes and pyenv shims |
| #408 | feature | +1146/-15 | 2 | 2 | 1 | 0 | 0.2 | ☕ Give the validator one sandboxed execution entry point |
| #407 | feature | +732/-89 | 3 | 1 | 1 | 0 | 5.4 | ☕ Room acts as a GitHub App bot for the author's fix |
| #406 | docs | +323/-39 | 1 | 1 | 0 | 0 | 0.3 | ☕ Trim the Multi-agent PR page and drop the Mermaid note |
| #405 | feature | +419/-25 | 1 | 0 | 0 | 0 | 0.1 | ☕ Review refuses a head that adds nothing over its base |
| #404 | docs | +252/-0 | 7 | 3 | 1 | 0 | 56.6 | ☕ Add a public page for the shipd-axel GitHub App |
| #403 | docs | +260/-3 | 1 | 0 | 0 | 0 | 0.2 | ☕ Skip the doctor pipeline check on an unloadable config |
| #402 | docs | +260/-2 | 1 | 0 | 0 | 0 | 0.2 | ☕ Document doctor skips on an unresolvable content dir |
| #401 | docs | +41/-4 | 1 | 0 | 0 | 0 | 0.1 | ☕ Keep shipd doctor running when dir is invalid |
| #400 | epic bookkeeping | +11/-9 | 1 | 0 | 0 | 0 | 0.0 | ☕ Sync the shipd-init epic status to complete |
| #399 | feature | +1126/-65 | 2 | 0 | 0 | 0 | 0.2 | ☕ Add the /s:init setup skill and shared needs-setup check |
| #398 | feature | +2508/-92 | 3 | 3 | 1 | 2 | 0.4 | ☕ Add shipd config set/unset/check and one config writer |
| #397 | epic bookkeeping | +15/-1 | 1 | 0 | 0 | 0 | 0.0 | ☕ Sync the shipd-init epic status to active |
| #396 | feature | +968/-21 | 2 | 2 | 1 | 0 | 0.3 | ☕ Add shipd init status and unattended autopilot sessions |
| #395 | epic bookkeeping | +8/-1 | 1 | 1 | 0 | 0 | 0.0 | ☕ Amend shipd-init: strict config writes, registered statusl |
| #394 | epic bookkeeping | +139/-0 | 2 | 1 | 0 | 0 | 0.0 | ☕ Add the shipd-init epic for guided setup and config contro |
| #393 | research | +172/-0 | 2 | 0 | 0 | 0 | 0.5 | ☕ Research how optional shipd add-ons should work |
| #392 | feature | +507/-241 | 1 | 0 | 0 | 0 | 0.1 | ☕ Drop the question rejection recovery rule |
| #391 | feature | +505/-62 | 1 | 0 | 0 | 0 | 0.1 | ☕ Remove Claude mentions from generic skill prose |
| #390 | feature | +2127/-988 | 2 | 0 | 0 | 0 | 0.3 | ☕ Replace the oracle agent with an inline oracle-lookup verb |
| #389 | epic bookkeeping | +16/-1 | 1 | 0 | 0 | 0 | 0.0 | ☕ Close epic context-budget |
| #388 | feature | +656/-268 | 3 | 3 | 1 | 0 | 0.4 | ☕ Trim skill descriptions to a 300-character budget |
| #387 | feature | +792/-9 | 1 | 2 | 0 | 0 | 0.3 | ☕ Skip claude-code user files when the s@shipd plugin is ins |
| #386 | feature | +245/-3 | 1 | 0 | 0 | 0 | 0.1 | ☕ Skip drift paths outside the repository |
| #385 | epic bookkeeping | +20/-43 | 1 | 0 | 0 | 0 | 0.0 | ☕ Re-scope the context-budget epic to the two listing fixes |
| #384 | epic bookkeeping | +69/-0 | 1 | 0 | 0 | 0 | 0.0 | ☕ Add the context-budget epic to measure and cut shipd's con |
| #383 | feature | +261/-32 | 3 | 1 | 0 | 0 | 0.3 | ☕ Move the risk rubric to /s:epic and rate stubs with it |
| #382 | feature | +940/-8 | 3 | 1 | 0 | 0 | 0.3 | ☕ Add /s:plan-deep and a risk report to the epic grill |
| #381 | research | +73/-0 | 1 | 0 | 0 | 0 | 0.0 | ☕ Add research on epic complexity rubrics and maps |
| #380 | feature | +378/-18 | 2 | 1 | 0 | 0 | 0.3 | ☕ Find the live session's transcript by its session id in bu |
| #379 | docs | +364/-6 | 2 | 2 | 0 | 0 | 0.1 | ☕ Add a walkthrough for multi-agent autonomous pull requests |
| #378 | feature | +2547/-24 | 4 | 10 | 2 | 0 | 1.3 | ☕ Claim each review head through GitHub so one review posts |
| #377 | feature | +403/-13 | 2 | 1 | 0 | 0 | 2.1 | ☕ Lock room run per repository and agent |
| #376 | docs | +115/-4 | 1 | 0 | 0 | 0 | 0.1 | ☕ Say where the early skills lived before automikk |
| #375 | docs | +263/-8 | 2 | 1 | 0 | 0 | 0.2 | ☕ Add Episode 0 intro and the shipd history page |
| #374 | feature | +991/-56 | 5 | 1 | 0 | 0 | 0.6 | ☕ Brand the CI gate review and route room reviews through sh |
| #373 | feature | +422/-3 | 4 | 2 | 0 | 0 | 0.5 | ☕ Make the bundled room.py run fail with one clear error |
| #372 | feature | +683/-2 | 2 | 0 | 0 | 0 | 0.2 | ☕ Stop writing skills cleanly under Claude Code plan mode |
| #371 | feature | +1477/-62 | 1 | 0 | 0 | 0 | 1.2 | ☕ Add a repo-wide reviewer mode to shipd room run |
| #370 | feature | +507/-103 | 1 | 0 | 0 | 0 | 0.3 | ☕ Resolve the gate's superseded threads in their own job |
| #369 | feature | +352/-52 | 1 | 0 | 0 | 0 | 0.2 | Request a re-review on any push to the head in an author roo |
| #368 | docs | +281/-11 | 1 | 0 | 0 | 0 | 0.1 | shipd doctor: report a protected branch as protected without |