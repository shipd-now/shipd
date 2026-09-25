# doctor-autofix
Status: verified
Theme: developer-experience

## Idea

Give `shipd doctor` a `--fix` mode that provisions the environment
autonomously and ends by delegating to the drive preflight.

### Motivation

Standing up a shipd machine means running three separate doctors and
hand-installing whatever each reports missing. No single command gets an
environment ready, and `shipd doctor` does not even know the drive toolchain
exists.

### Details

- Add `--fix` to the binary's `doctor` verb. Bare `doctor` stays read-only.
- Under `--fix`, run every local-tooling remedy without asking: the `textual`
  install, the tiered `semdiff doctor --fix` for `difft`, and
  `shipd statusline install`.
- Report, never perform, the two GitHub-side mutations (`protection`,
  `automerge`) and every finding with no automated remedy, naming the surface
  each absence affects.
- Continue past a failed remedy rather than aborting, then re-run the checks
  and exit on the repaired state.
- Delegate to `drive.py doctor --fix` as the final step, and widen that verb
  to install `ffmpeg`, `ffprobe`, and `vhs` rather than only the browser.

Affected capabilities: `shipd-cli` (modified), `shipd-doctor` (modified),
`shipd-drive` (modified). Impact: `plugins/s/bin/shipd`,
`plugins/s/skills/drive/scripts/drive.py`,
`plugins/s/skills/build/tests/test_shipd_cli.py`,
`plugins/s/skills/drive/tests/test_drive_cli.py`. No new dependencies.

### Non-goals

- No change to bare `shipd doctor`. It reports, installs nothing, and reaches
  no network, so `/s:build` and CI keep their current contract.
- No GitHub-side mutation from the autonomous mode. Branch protection and
  auto-merge stay with the consent-gated `/s:doctor` and `/s:gate`.
- No removal of the `/s:doctor` skill's consent round. It remains the
  interactive front door and the only path to the repository mutations.
- No new policy on optional tools. Each delegated installer keeps its own
  scope, so `rg` stays optional because `semdiff` says so.

## Implementation

- **`--fix` is the mutation gate, matching every sibling doctor.** All three
  — `semdiff doctor --fix`, `video_ingest.py doctor --fix`, and
  `drive.py doctor --fix` — state that network access occurs only under
  `--fix`. Putting provisioning on the bare verb instead would make a
  preflight mutate the machine, and the bare verb is what `/s:build` and CI
  call. Rejected: changing bare `doctor`, and removing the skill's consent
  round; each contradicts a verified requirement outright.
- **The split is by blast radius, not by caller.** A local install is
  reversible and machine-scoped; a branch-protection write changes a shared
  repository for every contributor. So `--fix` installs tools and registers
  the statusline, and leaves both `gh api` mutations to the consent round.
  Report-only-with-impact is not new machinery: `doctor-remedy-boundaries`
  already mandates that exact shape for a non-admin token.
- **Failures degrade, never abort.** Each remedy's outcome is recorded and
  the loop continues, so one unavailable installer cannot strand the rest.
  The verb re-runs the checks afterwards and exits on the repaired state,
  because the first pass's exit code describes a machine that no longer
  exists.
- **Delegation is a subprocess, not an import.** The binary is stdlib-only
  and resolves siblings through `PLUGIN_ROOT`, the same shape its other
  delegating verbs use. A missing drive CLI is one more reported finding.
- **Widening `drive.py doctor --fix` is required, not incidental.** Its
  current scope installs the browser alone and explicitly refuses `vhs`, so
  delegating to it unchanged would leave exactly the tools this change exists
  to install. The widened verb reports an install failure with the surface it
  affects and continues, mirroring the aggregator.
- Risk: `--fix` runs package-manager commands unattended, so a wedged
  package manager could hang the verb. Guarded by the continue-on-failure
  rule and by each delegated installer owning its own timeout behavior; the
  aggregator adds no new network path of its own.

## Questions and answers

### Q1: Where does the autonomous installer live?
- **Question:** `shipd doctor` is contractually read-only in three places,
  with remediation living in the consent-gated `/s:doctor` skill. Where
  should autonomous provisioning live? Options: (a) a new
  `shipd doctor --fix`; (b) make bare `doctor` install; (c) drop the skill's
  consent round. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a), `shipd doctor --fix`. The bare verb stays read-only
  and exit-code-compatible for the build flow and CI; every mutation and all
  network access happens only under the explicit `--fix` word, the invariant
  all three sibling doctors already carry verbatim. Options (b) and (c) each
  contradict a verified requirement: (b) reverses the read-only mandate, (c)
  removes the per-remedy consent the doctor skill is built around. Two
  consequences: the closing sentence of `doctor-remedy-boundaries` must be
  amended, and delegating to the drive preflight installs nothing beyond the
  browser unless that verb's own scope widens in the same change.
- **Cited:** verified/semantic-review, verified/video-pipeline,
  verified/shipd-cli, verified/shipd-doctor, queue
  q-demo-video-vhs-dependency-doctor-placement

### Q2: What may the autonomous mode do without asking?
- **Question:** The checks span local tool installs and GitHub repository
  mutations (the branch-protection write and the auto-merge PATCH). What may
  run unattended? Options: (a) local tooling only; (b) everything with an
  automated remedy; (c) local plus GitHub where the user owns the repo.
  Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a), local tooling only. The mode may install local
  tools and register the statusline without asking, and must treat both
  GitHub-side mutations as report-only, naming the affected surface and
  leaving them to the consent-gated doctor and gate skills. The repository
  already draws that line: an unattended `--fix` installing local
  prerequisites is blessed, while every surface offering those two `gh api`
  calls binds them to an explicit consent option. Option (c) finds no support
  — the gate skill's consent requirement is unconditional on ownership.
- **Cited:** verified/video-pipeline, verified/shipd-doctor,
  verified/shipd-gate, queue q-demo-video-vhs-dependency-doctor-placement

## Readiness attestation

### Problem and motivation

No single command provisions a shipd machine, and the environment preflight
does not cover the drive toolchain at all.

Evidence:

- `plugins/s/bin/shipd`'s `cmd_doctor` takes no arguments beyond `-h` and
  documents itself "Read-only: nothing here installs or edits."
- `shipd doctor` run in this repo reports none of `vhs`, `ffmpeg`, or the
  Playwright browser — they belong to a separate preflight.

### Scope and non-goals

The change adds a flag, an autonomous remedy loop, a delegation step, and a
widened drive install scope. Bare `doctor` and the skill's consent round are
untouched.

Evidence:

- In scope: `plugins/s/bin/shipd`,
  `plugins/s/skills/drive/scripts/drive.py`, and both test suites.
- Out of scope: `plugins/s/skills/doctor/SKILL.md` keeps its consent round
  and its GitHub remedies.

### Affected capabilities and files

Three capabilities carry the change: the binary's verb contract, the skill's
boundary sentence, and the drive preflight's install scope.

Evidence:

- Capability `shipd-cli`: `doctor-verb` (base bbb87e00c7ee).
- Capability `shipd-doctor`: `doctor-remedy-boundaries` (base a1e298d543d4),
  whose closing sentence forbids exactly this change as written.
- Capability `shipd-drive`: `drive-doctor` (base 014dcefe3cc0), whose
  scenario forbids installing `vhs` under `--fix`.
- Runnable premise: `shipd doctor --help` prints
  `usage: shipd doctor [-h]` and "Reports only." — no `--fix` exists today.
- Runnable premise: `drive.py doctor --fix` on a complete toolchain printed
  "performs no network access — the Playwright browser binary is already
  installed" and reported all five prerequisites present, so delegation is
  idempotent.
- Runnable premise: `semdiff.py doctor` exits 0 reporting git, difft and gh
  present and `rg` optional-and-absent, so the delegated installers keep
  their own scope.
- Runnable premise: `plugins/s/bin/shipd` imports thirteen stdlib modules
  and nothing else, and resolves siblings through `PLUGIN_ROOT`, so it can
  invoke the drive CLI as a subprocess without a dependency.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Where the autonomous installer lives: settled by the oracle, Q1.
- What it may mutate without asking: settled by the oracle, Q2.
- Optional-tool policy: resolved by delegation, since each installer keeps
  its own scope rather than the aggregator inventing one.
