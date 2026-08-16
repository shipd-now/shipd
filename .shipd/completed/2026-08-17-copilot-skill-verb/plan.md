# copilot-skill-verb

Status: verified

## Idea

Add a `copilot` verb to the `shipd` binary that installs, reports on, and
removes the shipd semantic-review agent skill in a target repository, so
GitHub Copilot code review runs the same semdiff-grounded review there.

### Motivation

The research report `research/copilot-code-review` confirmed Copilot code
review executes agent skills from `.github/skills/` on Actions runners whose
tools a `copilot-code-review.yml` workflow preinstalls, but shipd offers no
way to install or maintain those files in a repo. A curated `shipd copilot`
verb makes the integration a one-command, upgradeable, reversible install.

### Details

- Add `copilot` to the binary's curated verbs: bare report, `add`, `remove`,
  all over `--root DIR` (default cwd), with `--force` on the mutating words.
- `add` writes three files into the target: `.github/skills/code-review/
  SKILL.md`, `.github/skills/code-review/scripts/semdiff.py` (byte copy of
  the plugin's engine), and `.github/workflows/copilot-code-review.yml`.
- Ship the two templates in the plugin at `plugins/s/integrations/copilot/`.

Affected capabilities: `shipd-cli` (modified), `copilot-review-skill` (new).
Impact: `plugins/s/bin/shipd`, `plugins/s/integrations/copilot/`,
`plugins/s/skills/build/tests/test_copilot_verb.py`, plugin version bump.

### Non-goals

- No model configuration (Q3): the code-review surface has no repo-side model
  pin; the installed SKILL.md documents that fact instead.
- No gate integration (Q2): Copilot review is advisory; `review_gate.py`'s
  `semantic-review` status remains the merge gate, untouched.
- No GitHub settings/ruleset mutation and no `gh` calls: the verb writes
  working-tree files only; enabling automatic review stays a user action.
- No changes to `/s:review` or `semdiff.py` itself, and no install into this
  repo as part of this change.

## Implementation

- **In-binary verb, statusline pattern.** `cmd_copilot` lives in `bin/shipd`
  beside `cmd_statusline` (no engine-script delegation: it manipulates target
  repo files, not spec artifacts), stdlib-only per the constitution. Bare
  invocation is read-only; only the explicit words `add`/`remove` mutate.
  Rejected: an engine script under `skills/build/scripts/` — the engine is
  the spec library's domain and this writes none of it.
- **Ownership markers gate every mutation.** The SKILL.md template carries the
  line `<!-- shipd-copilot v{version} -->` and the workflow template the line
  `# shipd-copilot v{version}`; `add` substitutes `{version}` with the plugin
  manifest version (same read as `cmd_version`). A target file that exists
  without its marker is foreign: `add` and `remove` refuse with exit 1 naming
  it, unless `--force`. Marked files are refreshed/deleted freely, so re-`add`
  is the upgrade path and both words are idempotent. `semdiff.py` carries no
  marker (kept byte-identical to the plugin's copy for drift comparison); it
  is owned by its parent skill directory's marked SKILL.md.
- **Report contract.** Bare `shipd copilot` prints one line per managed file:
  `installed` (marker version equals plugin version; semdiff bytes equal),
  `stale <ver>` (older marker or differing semdiff bytes), `foreign` (exists,
  no marker), or `absent` — then what `add` would write, a pointer that
  automatic review is enabled via a GitHub branch ruleset, and the Q3 note
  that the code-review surface exposes no repo-side model selection. Exit 0.
- **Writes are atomic** — same-directory temp file and `os.replace`, parents
  created, mirroring `_write_settings` (`bin/shipd:490-513`). `remove` also
  prunes the emptied `.github/skills/code-review/` tree (only when empty).
- **Templates are assets, not literals in code.** `plugins/s/integrations/
  copilot/SKILL.md` and `copilot-code-review.yml` are read at install time and
  resolved relative to the binary's plugin root, so checkout and cache
  snapshot installs behave alike. The workflow installs difftastic from its
  prebuilt release tarball (the same source `semdiff.py doctor --fix` uses)
  plus ripgrep via apt; degradation stays safe — `semdiff.py doctor` observed
  exiting 0 with difft merely `recommended` (text-engine fallback).
- **Usage banner and docstring** gain the verb; the docstring's "one deliberate
  exception" note becomes two (statusline, copilot) — both write user-domain
  files, never spec artifacts.
- **Risk:** a future semdiff.py change makes installed copies stale; the
  report's drift line plus re-`add` is the maintenance loop, and the version
  bump ships the newer engine to the plugin cache.

## Questions and answers

### Q1: What should the feasibility session deliver?
- **Question:** Deliver a buildable change immediately, an installed cited
  research report first, or findings only? Recommendation: the change.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Install the cited research report first; externally sourced,
  version-sensitive feasibility claims land as an installed report a later
  plan links, not as uncited plan prose. (Delivered: `research/
  copilot-code-review`, PR #51, merged.)
- **Cited:** verified/shipd-research, verified/shipd-epic

### Q2: What merge-gating posture for the Copilot-side review?
- **Question:** Advisory alongside the required `semantic-review` status,
  replacement, or dual-gate? Recommendation: advisory.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Advisory only. The gate is durably bound to `review_gate.py`'s
  contract (disposition scopes, thread resolution, branch protection);
  a Copilot run has none of that machinery, so promoting it would be a
  deliberate later spec change.
- **Cited:** verified/semantic-review

### Q3: What model configuration ships in v1?
- **Question:** Write an optional `.github/agents/` custom agent with `model:`
  frontmatter, no model config, or a placeholder key? Recommendation: the
  custom agent.
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** No model config in v1. The custom-agent mechanism is not
  documented for the code-review surface, so a `--model` flag would be a
  misleading name-to-effect mapping, and a placeholder is dead config;
  document the absence in the installed SKILL.md and revisit when GitHub
  exposes a real option.
- **Cited:** research/copilot-code-review, verified/shipd-install
