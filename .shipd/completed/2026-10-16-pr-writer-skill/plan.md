# pr-writer-skill
Status: verified
Epic: pr-conversations
Theme: developer-experience
Planned-at: 4dbd39712940f796520736363a14f1de45156124
Gated-hash: 4e32d6fed727

## Idea

Add a `/s:pr` skill that writes a shipd pull request's title and `## ☕ Shipd Pull Request` body, a `pr` config key for the title template, and switch every pull-request-opening flow from `gh pr create --fill` to it.

### Motivation

A person who opens a shipd pull request sees a description that reads like a stray comment under a title that cannot carry a ticket number, so they cannot tell what the change does or find it in their tracker. One writer, held to the documentation standard, fixes every flow at once.

### Details

- New skill `plugins/s/skills/pr/` (`SKILL.md`, `scripts/pr_title.py`, `tests/`), a harness body and reference, and a `shipd-pr` capability.
- New top-level config key `pr` (`title`, `ticket_pattern`) with a `resolve_pr(root)` accessor in `spec_common.py`, registered, documented in the example config, `docs/customise.md`, and `.shipd/README.md`.
- Callers switch to `/s:pr`: `/s:build` (auto, draft, epic-close), its harness body and reference, `worktree.sh` next steps, `/s:gate` (both fallbacks) and its body, `/s:epic` amend, `/s:initiative` set, the autopilot build prompt, and `AGENTS.md`.
- Registered in the `AGENTS.md` skill sentence, the README table, and the cheatsheet. Plugin version bumps one patch above `main`.

Affected capabilities: `shipd-pr` (added), `shipd-config` (modified by one added requirement).

### Non-goals

- `/s:pr` does not push, arm auto-merge, or read `pr-mode`; callers keep that.
- No change to `pr-mode`, the review gate, or any room verb.
- No rewrite of descriptions on pull requests that already exist, other than the one `/s:pr` is run on.

## Implementation

- **Invocation.** `/s:pr [--ticket <id>] [--draft] [--base <ref>]`. It reads the change (`spec_status.py cat change <slug>` when the branch is `change/<slug>`, else `git log <base>..HEAD`), drafts a body, lints it, then runs `gh pr create --title … --body-file …` (plus `--draft`). When the branch already has a pull request it runs `gh pr edit` instead. It prints the full URL. Callers push first and arm auto-merge after (Q1).
- **Body.** Line 1 `## ☕ Shipd Pull Request`, a why-first paragraph, a short list of what changed, then `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. It reads `${CLAUDE_PLUGIN_ROOT}/skills/document/references/standard.md` first. The body is staged with `<!-- doc-type: concept -->` as line 1, `docs_lint.py` runs until exit 0, and the marker line is stripped before posting (Q3).
- **Title.** `scripts/pr_title.py` (stdlib) exposes `find_ticket(pattern, branch)`, `render_title(template, summary, ticket, change)`, and the CLI `pr_title.py [--root R] title --summary S [--ticket T] [--branch B]`, which resolves the template through `resolve_pr`, takes the ticket from `--ticket` else the first `ticket_pattern` match in the branch, and prints the title. With no ticket, `{ticket}` and the whitespace after it drop out. `{change}` is the slug of a `change/<slug>` branch, else empty. Whitespace collapses; an empty result exits 1. The summary is the plan's one-sentence summary, trimmed by the skill to about 60 characters.
- **Config.** `PR_KEY = "pr"` joins `RECOGNIZED_CONFIG_KEYS`. `resolve_pr(root)` returns `(title, ticket_pattern)` with defaults `("{summary}", None)`. Strict like `resolve_room`: a non-object, a non-string title, a placeholder outside `{ticket}`, `{summary}`, `{change}`, a title without `{summary}`, or a `ticket_pattern` that is not a string or does not compile raises `ConfigError` naming `pr`, the member, and the file (Q4). Other members are ignored.
- **Callers.** Every `gh pr create --fill` in `plugins/s` and `AGENTS.md` becomes "open it with `/s:pr`" (`--draft` in draft mode). Metadata PRs use it too (Q2). A test fails if `gh pr create --fill` reappears outside tests.
- **Harness.** `bodies/pr.md` follows `bodies/room.md`; no `subagent` wording in ungated text.

Risk: skills load from the cached snapshot, so the version bump is part of the change. Guard: `version_guard.py`.

## Questions and answers

### Q1: Does /s:pr push and arm auto-merge?
- **Question:** Create or update only, with callers pushing first and arming auto-merge after (1), or push and arm inside `/s:pr` (2)? Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. The epic scopes `/s:pr` to writing the title and body, and callers use it in place of the create step only.
- **Cited:** epic/pr-conversations

### Q2: Do metadata PRs call /s:pr?
- **Question:** Do epic-amend, epic-close, initiative-set, and gate fallback pull requests call `/s:pr` (1), or only change-shipping ones (2)? Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. The epic says every skill that opens a pull request calls `/s:pr`; the oracle noted the wording is unqualified rather than explicit about metadata PRs.
- **Cited:** epic/pr-conversations

### Q3: How is the body checked against the documentation standard?
- **Question:** Stage the body with a `<!-- doc-type: concept -->` first line, lint it, and strip the marker before posting (1), or add a PR-body mode to `docs_lint.py` that skips the marker rule (2)? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The lint stays unchanged, since docs CI shares it. The planner adopted this default.
- **Queued:** q-pr-body-docs-lint-marker

### Q4: How strictly is the `pr` key validated?
- **Question:** Strict `ConfigError` for bad members, as `resolve_room` does (1), or ignore bad members and use defaults (2)? Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. A silently ignored bad template would give unreadable titles with no signal, and `room` and `pr-mode` already fail loudly. The planner adopted this default.
- **Queued:** q-pr-config-key-validation-strictness

## Readiness attestation

### Problem and motivation

Shipd pull requests open with `gh pr create --fill`, so their descriptions are commit text and their titles cannot carry a ticket.

Evidence:

- Epic `pr-conversations`, Decisions "A pull request describes itself" and "Titles follow a configurable template".
- `plugins/s/skills/build/SKILL.md:643` and `:682` run `gh pr create --fill`.

### Scope and non-goals

The change adds one skill, one config key, and call-site edits. Pushing, auto-merge, `pr-mode`, and the room verbs stay out.

Evidence:

- In scope: `plugins/s/skills/build/scripts/spec_common.py:407` (registry), `:1098` (`pr-mode` pattern to follow).
- Out of scope: `plugins/s/skills/room/` and `review_gate.py` are not edited.

### Affected capabilities and files

`shipd-pr` is new and `shipd-config` gains one requirement.

Evidence:

- `grep -rn "gh pr create" plugins/s` found sites in `skills/build/SKILL.md`, `skills/build/scripts/worktree.sh:759`, `skills/gate/SKILL.md:149,355`, `skills/epic/SKILL.md:163`, `skills/initiative/SKILL.md:220`, `harness/bodies/build.md:103`, `harness/bodies/gate.md:37`, `harness/references/build.md:57,71`.
- Registration surfaces: `AGENTS.md` skill sentence, `README.md` Orchestration table, `docs/cheatsheet.md` table and group list, as `/s:room` did in commit fdfa616.
- Runnable premise: `python3 plugins/s/skills/document/scripts/docs_lint.py body.md` with a body lacking a marker → exit 1, "missing first-line doc-type marker"; with `<!-- doc-type: concept -->` on line 1 → exit 0.

### No open task-shaping decision

Every decision is settled; none remain.

Evidence:

- Push and merge ownership: oracle, Q1. Metadata PRs: oracle, Q2.
- Lint approach: planner default, Q3. Config strictness: planner default, Q4.
