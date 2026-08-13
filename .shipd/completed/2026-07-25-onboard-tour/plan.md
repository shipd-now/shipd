# onboard-tour
Status: verified
Theme: developer-experience

## Idea

A new user has no way to learn shipd: `am:hello` only proves the plugin is
wired, and the working knowledge — what a change is, how the lifecycle runs,
what epics/initiatives/workspace add, how a plan/build session actually feels
— is scattered across `am/README.md`, `AGENTS.md`, and skill internals.
Nothing steps a person through a session.

This change adds guided onboarding, per the depth-path decisions confirmed
with the user:

- A **`docs/onboarding/` chapter library** — six numbered markdown chapters
  (concepts; artifacts & lifecycle; planning; building; epics, initiatives &
  workspace; workflow) that are the single source of tour content.
- An **`/s:onboard` tour skill** that loads the chapters in order — linear
  with an upfront skip menu and a checkpoint after each chapter — and
  illustrates each one from the user's live repo state.
- A **sandbox hands-on finale**: the tour scaffolds a throwaway mini-repo
  with its own `am/` layout and toy capability, guides a real plan → build →
  merge cycle there with the plugin's own engine scripts, and offers cleanup.
- **`am:hello` is retired** (`plugins/s/commands/hello.md` deleted);
  `/s:onboard` is the entry point.
- Plugin version bump (0.2.5 → 0.2.6, or one patch above whatever
  `origin/main` carries at ship time).

### Non-goals

- No restating of grammar in docs: chapters narrate and point at the
  authoritative files (`am/README.md`, `AGENTS.md`), so they cannot drift
  into a second grammar definition.
- No changes to the engine scripts, existing skills, or lint — this change
  is docs + one new skill + one deletion.
- No video/web assets; markdown only.
- No auto-launch of the tour; it runs only when invoked.

Affected capabilities: `shipd-onboard` (new). Impact: `docs/onboarding/`
(new, six files), `plugins/s/skills/onboard/SKILL.md` (new),
`plugins/s/commands/hello.md` (deleted),
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Docs are the content; the skill is the delivery.** Each chapter file
  carries the teaching narrative; `SKILL.md` instructs the tour to read the
  chapter file, teach it conversationally, illustrate it from the live repo
  (e.g. list the user's real `am/verified/` capabilities in chapter 2, run
  `epic-show`/`workspace-show` in chapter 5 when those exist), and pause at
  a checkpoint. Rejected: content inside `SKILL.md` — it would duplicate
  docs/ and bloat the skill's context load; loading one chapter at a time
  keeps context lean.
- **Chapter set and file names are fixed** (the skill references them):
  `docs/onboarding/01-concepts.md`, `02-artifacts.md`, `03-planning.md`,
  `04-building.md`, `05-scaling.md`, `06-workflow.md`. Each opens with a
  2–3 sentence "what you'll learn", teaches, and ends with "authoritative
  references" links.
- **Skip menu and checkpoints via AskUserQuestion.** The tour opens with a
  chapter menu (start-to-finish recommended first); each checkpoint offers
  continue / re-explain / jump / stop. The tour never assumes; a user can
  leave at any checkpoint.
- **Sandbox mechanics** (chapter 6's hands-on, in `SKILL.md`): create a temp
  directory (the session scratchpad when available, else `mktemp -d`), `git
  init`, scaffold `am/verified/greeter/spec.md` (one toy requirement with a
  scenario) and empty `am/planned/`; then guide the user to plan a toy
  change (add a farewell requirement) — authoring the three artifacts
  together, linting with `spec_lint.py <change> --root <sandbox>` — and
  build it: tick tasks via `claim_task.sh` from the sandbox root, drive
  statuses with `spec_status.py`, finish with `spec_merge.py` and show the
  archived change. All scripts are invoked by absolute plugin path, so the
  sandbox exercises the real engine. End by offering to delete or keep the
  sandbox. Rejected: driving `/s:plan`//`/s:build` skills inside the
  sandbox — they carry worktree/PR ceremony that has no meaning in a temp
  repo; the tour teaches the artifact flow directly and points at the real
  skills for real work.
- **Retirement is spec-pinned.** Deleting `commands/hello.md` is enforced by
  a scenario, so the toy command cannot quietly return; the plugin's
  command list then shows only real entry points.
- **Version bump rule, not number:** set `plugin.json` to one patch above
  the higher of the worktree's value and `origin/main`'s value at ship time
  — main has been moving between concurrent sessions (see #15/#16), and the
  hard-coded-number lesson from PR #11 is codified here.
- **Risk:** chapters drifting as features evolve — mitigated by the
  narrate-and-point rule (Non-goals) and by illustrating from live state;
  a stale chapter shows its age immediately against real output.
