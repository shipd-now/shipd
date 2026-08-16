# Running the shipd semantic review inside GitHub Copilot code review

## Summary

It is feasible to run the shipd semantic review engine inside GitHub Copilot
code review as an agent skill. As of July 29, 2026, agent skills and MCP server
support for Copilot code review are generally available on all paid Copilot
plans (Pro, Pro+, Business, Enterprise) [1]. Agent skills are "folders of
instructions, scripts, and resources that Copilot can load when relevant", and
they explicitly work with Copilot code review (alongside the cloud agent, the
Copilot CLI, and agent mode in IDEs) [2]. Copilot code review runs on GitHub
Actions runners, and a repository can preinstall tools and dependencies into
the review environment through a `.github/workflows/copilot-code-review.yml`
workflow (falling back to `copilot-setup-steps.yml` when the review-specific
file is absent) [3][4] — which is where `difftastic` (`difft`) would be
provisioned. The shipd side already fits this shape: `semdiff.py` is
stdlib-only Python, all its review subcommands are read-only, and it degrades
gracefully to a text engine when `difft` is missing.

The main constraints are: skill invocation is relevance-driven rather than
deterministic — "existing agent skills within the `.github/skills` directory
will automatically be available to use by Copilot code review if relevant to
the review", with a `code-review`-named skill subdirectory recommended to
ensure the skill is read [5]; all MCP tool calls made by code review are
read-only [1]; and a network firewall is enabled by default for the review
environment [4]. The largest gap is that Copilot posts its own PR review —
none of the shipd gate machinery (`review_gate.py`'s `semantic-review` commit
status, disposition scopes, and thread-resolution contract) has a Copilot-side
counterpart, so a Copilot-hosted run is an advisory review signal, not a
replacement for the existing required merge gate.

## Agent skill support in Copilot code review

- Agent skills and MCP support for Copilot code review reached general
  availability on July 29, 2026, "for all Copilot Pro, Pro+, Business, and
  Enterprise users" [1]; the public preview was announced June 2, 2026 [5].
- Skills live in per-skill subdirectories under `.github/skills`, each with a
  `SKILL.md` carrying "relevant context and instructions" [5]. GitHub's skill
  loader also reads project-level `.claude/skills` and `.agents/skills`
  locations [2] — notable for shipd, whose review skill already exists in
  Claude's `SKILL.md` format.
- Skills are defined as "folders of instructions, scripts, and resources that
  Copilot can load when relevant to improve its performance in specialized
  tasks" [2] — i.e. a skill may bundle executable scripts, which is the
  mechanism by which `semdiff.py` (or a trimmed copy of it) would be shipped
  and run during a review.
- Skills let code review "invoke your team's internal tools and coding
  standards during a review" [1].

## The execution environment — runners, setup steps, tool installation

- Copilot code review "operates on GitHub Actions runners by default",
  consuming Actions minutes on private repositories [3].
- Two workflow files configure the review environment:
  `copilot-code-review.yml` is primary, and the coding agent's
  `copilot-setup-steps.yml` is the fallback when it is absent [3][4]. The
  review file lets teams "configure the environment available to Copilot code
  review during runtime", including dependency installation and tooling
  setup [4] — so `difft` can be preinstalled (e.g. from difftastic's release
  binaries, matching what `semdiff.py doctor --fix` already automates), along
  with `ripgrep` for `semdiff context`.
- Runner type is configurable at the organization level, now split into
  independent sections for code review versus the cloud agent [4]. Self-hosted
  runners are supported only through Actions Runner Controller (ARC) on
  Ubuntu x64 Linux — "ARC is the only officially supported solution for
  self-hosting Copilot code review" [3].
- Default hosted runners are Linux; `semdiff.py` needs only Python 3 and git,
  both standard on Actions runners, and its difftastic dependency is
  "recommended, never required" by design (text-engine degradation).

## Instruction surfaces — where the review rubric would live

- Copilot code review reads repository-wide custom instructions
  (`.github/copilot-instructions.md`), path-specific
  `.github/instructions/**/*.instructions.md`, agent skills, and a repo-root
  `AGENTS.md` for "always-on rules shared across AI agents" [6]; since
  July 17, 2026 it also picks up `REVIEW.md`, `GEMINI.md`, and `CLAUDE.md`
  files automatically [4].
- Instructions, skills, and `AGENTS.md` are read from the pull request's
  **head branch**, not the base branch [6][4] — so a PR that changes the
  review skill exercises the changed skill in its own review.
- This is where the `/s:review` judgement layer (cohort ordering, the
  high/medium/low severity rubric, the ship-it/fix-required verdict contract,
  spec-aware scenario verification) would be restated as review instructions;
  the skill's `SKILL.md` would direct Copilot to run the bundled `semdiff`
  subcommands (`files`, `diff`, `context`, `change`) instead of reading raw
  file dumps.

## Constraints and limits

- **Non-deterministic invocation.** Skills are used "if relevant to the
  review" [5]; GitHub recommends a `code-review`-named skill subdirectory to
  "ensure that Copilot code review will read and utilize the skill" [5], and
  clear signals (review-focused skill names, custom instructions referencing
  the skill) make use more likely [6]. There is no documented guarantee the
  skill runs on every review.
- **Read-only MCP.** "All MCP tool calls performed by Copilot code review will
  be limited to read-only"; the GitHub and Playwright MCP servers are enabled
  by default, and MCP servers are configured in repository settings with
  tokens stored as agent secrets [1]. The shipd engine is unaffected: it is a
  local script, not an MCP server, and its review subcommands are read-only by
  design.
- **Firewall.** A network firewall is "enabled by default for all
  repositories", configured under repository settings → Copilot → Internet
  access; self-hosted runners do not currently support the firewall [4].
  Organizations must allow the standard Actions hosts plus
  `api.githubcopilot.com`, `uploads.github.com`, and
  `user-images.githubusercontent.com` [3]. Tool installation therefore belongs
  in the setup-steps workflow rather than mid-review downloads.
- **Plan gating.** The feature requires a paid Copilot plan (Pro, Pro+,
  Business, Enterprise) [1].

## Mapping the shipd review system onto these mechanisms

- **`semdiff.py` → bundled skill script.** Ships inside
  `.github/skills/code-review/` (or is referenced in-repo, since the plugin
  source lives in this repository); the runner provides git and Python 3, and
  the setup workflow provides `difft`/`rg`.
- **`/s:review` SKILL.md judgement layer → Copilot instruction surface.** The
  rubric, cohort flow, and verdict contract translate to the skill's
  `SKILL.md` plus `REVIEW.md`/custom instructions [4][6].
- **`review_gate.py` → no counterpart; stays as-is.** Copilot code review
  posts its own review comments as the `copilot` reviewer; nothing in the
  fetched documentation lets a skill set a third-party commit status such as
  shipd's `semantic-review` context, drive its disposition scopes, or resolve
  gate threads. The existing `review_gate.py` merge gate would remain the
  required check, with the Copilot-side run as an advisory reviewer alongside
  it.

## Gaps & caveats

- No fetched source documents whether a code-review agent skill's bundled
  scripts run under time, output-size, or sandbox limits distinct from the
  Actions runner's own; treat script runtime limits as unverified.
- Whether Copilot code review can be made to emit machine-readable output (the
  `--json` verdict shape) or set commit statuses from a review run was not
  found in any fetched source; assume it cannot, pending testing.
- The strength of the "skills can bundle executable scripts" claim for the
  code-review surface specifically rests on the general agent-skills
  definition [2] plus "invoke your team's internal tools" [1]; no fetched page
  shows a worked example of code review executing a bundled script. A small
  spike PR would settle this empirically.
- How aggressively the default firewall restricts the review runtime (as
  opposed to the setup job) is not detailed in the fetched pages.
- Frequency/quality of skill invocation ("if relevant") is undocumented; a
  trial period alongside the existing gate is the only way to measure it.

## Sources

1. Copilot code review: Agent skills and MCP now generally available — GitHub Changelog — https://github.blog/changelog/2026-07-29-copilot-code-review-agent-skills-and-mcp-now-generally-available/
2. About agent skills — GitHub Docs — https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
3. Configuring runners for GitHub Copilot code review — GitHub Docs — https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/configure-runners
4. Copilot code review: Customization and configurability improvements — GitHub Changelog — https://github.blog/changelog/2026-07-17-copilot-code-review-customization-and-configurability-improvements/
5. Shape Copilot code review around your team — GitHub Changelog — https://github.blog/changelog/2026-06-02-shape-copilot-code-review-around-your-team/
6. About GitHub Copilot code review — GitHub Docs — https://docs.github.com/en/copilot/concepts/agents/code-review
