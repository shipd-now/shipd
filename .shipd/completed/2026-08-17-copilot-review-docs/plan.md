# copilot-review-docs

Status: verified

## Idea

Add `docs/copilot-review.md`, a human-facing guide to installing, enabling,
maintaining, and understanding the shipd semantic review inside GitHub
Copilot code review.

### Motivation

The `shipd copilot` verb (change `copilot-skill-verb`, PR #57) ships the
install/report/remove machinery, and the installed `SKILL.md` instructs the
*reviewing agent* — but no document tells the *user* how to set the
integration up end to end. The user asked for a `docs/copilot-review.md` so
they know how to install it.

### Details

- New `docs/copilot-review.md` covering, in order: what the integration is
  (an advisory Copilot-hosted run of the shipd review); prerequisites (a paid
  Copilot plan with code review, a GitHub-hosted repo); installing with
  `shipd copilot add` and what the three managed files are; committing and
  pushing them (Copilot reads skills and workflows from the PR **head**
  branch); enabling reviews (request Copilot as a reviewer on a PR, or a
  branch ruleset for automatic review); checking and upgrading with the bare
  `shipd copilot` report and re-`add`; uninstalling with `remove`; and scope
  and limits (advisory beside the `semantic-review` gate, no repo-side model
  selection, relevance-driven skill pickup, optional difftastic with safe
  text-engine degradation).

Affected capabilities: `project-readme` (modified — one ADDED requirement).
Impact: `docs/copilot-review.md` (new). Docs only — nothing under
`plugins/s/` changes, so no plugin version bump.

### Non-goals

- No links added *to* the guide from `README.md` or other docs —
  discoverability linking stays a follow-up, matching the
  `getting-started-docs` precedent.
- No changes to the `copilot` verb, the installed templates, or the research
  report; the guide documents shipped behavior only.
- No restating of the reviewing agent's instructions — the installed
  `SKILL.md` remains that authority; the guide describes what it does.

## Implementation

- **Facts come from shipped surfaces, not memory.** The guide's claims trace
  to: the `copilot-verb` and `copilot-review-skill` requirements in
  `.shipd/verified/` (managed files, report states, force semantics, marker
  ownership), the actual output of `plugins/s/bin/shipd copilot` (quoted
  report lines), and `.shipd/research/copilot-code-review/report.md`
  (plan availability, head-branch reading, relevance-driven pickup,
  `copilot-code-review.yml` as the environment workflow, advisory posture).
  Where the guide states a GitHub-side behavior, it should match the research
  report rather than inventing detail.
- **Command examples use the installed binary form** (`shipd copilot …`),
  with `--root` shown once for out-of-repo use; the default-cwd form is
  primary.
- **Tone and shape follow `docs/getting-started.md` / `docs/quickstart.md`**:
  task-ordered sections, short prose, fenced command blocks with the output
  the user should expect where it aids verification.
- **The advisory framing is load-bearing.** The guide must say plainly that
  Copilot's review does not replace the required `semantic-review` commit
  status and cannot set it — that is the durable Q2 decision from
  `copilot-skill-verb`.
