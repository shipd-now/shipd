# harness-install
Status: complete
Theme: developer-experience

## Introduction

shipd's whole user surface rides one harness: the Claude Code plugin carries
the `/s:` skills, and everything else — Cursor, Copilot, Windsurf, Aider,
Codex CLI, oh-my-pi, and the rest of the current agent ecosystem — has no way
to drive the spec engine at all. Meanwhile the curl install ends headless: it
registers the marketplace, installs the plugin, writes the launcher, prints a
tip block, and never asks the one onboarding question that matters — *where do
you actually work?* The engine itself is already portable (stdlib Python and
POSIX shell, worktrees included); what is missing is the instruction surface
that tells each harness's agent how to drive it.

This epic closes both gaps with one mechanism. A harness-adapter framework —
modeled on OpenSpec's `ToolCommandAdapter` pattern, rebuilt in the stdlib
Python binary — generates command files for eleven harnesses (oh-my-pi,
Cursor, Claude Code, GitHub Copilot, Windsurf, Aider, Codex CLI, Cline/Roo
Code, Continue.dev, Google Antigravity, Devin) from one shared set of
feature-gated command bodies. Each harness declares which features it
supports (sub-agents, question dialogs, on-demand file references, …), and
the generated files scale to that declaration: a harness without sub-agents
gets a body that never mentions them. On top of the framework, a new
interactive `shipd install` step — opened by an animated ASCII **SHIPD**
wordmark and run automatically at the end of `install.sh` — lets the user
pick their harnesses, records the selection, and writes the user-global
surfaces; a per-repo `shipd harness add` verb applies the project-level files
later, following the `copilot`/`vendor` verb family.

Intended outcome: a developer who runs the curl one-liner lands in a branded,
interactive finish that installs shipd into the harnesses they actually use —
and every one of those harnesses can plan, build, review, and inspect specs
by driving the same `shipd` CLI.

Success criteria:

- `curl … | sh` ends in the interactive `shipd install` (TTY only; headless
  runs degrade to the current non-interactive finish), opening with the
  animated wordmark and a working harness multi-select read from `/dev/tty`.
- `shipd harness add` installs the generated command set into a repository
  for every selected harness, idempotently, with ownership markers and
  `--force` semantics matching `copilot add`/`vendor add`.
- Generated files for a harness never mention a feature that harness did not
  declare; adding harness #12 requires only a new registry entry, no body
  edits.
- All engine tests keep passing with neither `textual` nor `pydantic`
  installed.

### Non-goals

- **No port of the plugin's skill implementations.** The generated commands
  are distilled bodies driving the `shipd` CLI, not copies of the `/s:`
  SKILL.md files; the plugin remains the engine's distribution vehicle and
  the authoring surface.
- **No package-manager distribution changes.** The marketplace plus
  `curl | sh` remain the vectors (per the `shipd-dx` epic); `claude plugin
  install` stays in `install.sh` — the launcher resolves the engine out of
  the plugin cache, so the plugin is load-bearing even for non-Claude users.
- **No third-party TUI dependency.** The install TUI is stdlib ANSI — no
  `textual`, no curses full-screen mode; the constitution's dependency
  exceptions do not widen.
- **No harness-specific engine features.** Adapters generate instruction
  files only; no MCP servers, per-harness APIs, or network fetches — 
  generation is local template rendering.
- **No rebrand.** The ☕ mark stays everywhere it is spec'd
  (`installer-brand-mark`, README, statusline); the wordmark is additive and
  confined to the install surface.
- The epic does not itself plan or build its member changes.

## Research

- [Architecting the Next-Generation Developer Experience for Agentic Development Tools](../../research/cli-developer-experience/report.md) — its installation-vector guidance (the `curl | sh` fallback and supply-chain cautions) and TUI discipline (progressive disclosure, adaptive color, restraint) bind the install-TUI member; its harness survey frames the ecosystem this epic targets.

## Decisions

- **Features are declared, not detected.** A canonical feature vocabulary
  (first cut: `subagents`, `question-dialogs`, `file-references` for
  on-demand reference loading, `background-tasks`; fixed during
  `harness-registry`) lives in the registry, and each harness entry declares
  the subset it supports. Command bodies are composed from feature-gated
  segments; a segment whose feature is undeclared is omitted entirely, so
  generated output never mentions an unsupported capability. Scaling to new
  harnesses or new features is a registry edit, not a body rewrite.
- **Progressive disclosure is the body architecture.** Each generated command
  is a lean router: the primary workflow inline, heavy fallback workflows
  externalized into reference files the agent reads only when a capability is
  missing (for dialects with `file-references`; dialects without it inline a
  compact degradation note instead). Frontmatter gating (`requires_tools`-
  style fields) is used where the dialect supports it. Degradation follows
  the three-step protocol: acknowledge the missing capability, state what
  would have run, offer the manual workaround.
- **Generated commands are the canonical user surface — Claude Code
  included.** Claude Code is adapter target #2 like any other harness: the
  TUI generates its user-global proxy commands with every feature enabled.
  The plugin remains installed (it carries the engine and the skill sources)
  but the generated set is the uniform way users drive shipd across all
  eleven harnesses.
- **Every skill is generated, capability-scaled.** All `/s:` commands get a
  generated counterpart per harness — none is Claude-only by fiat; bodies
  degrade per the feature declaration (e.g. build's delegated flow becomes a
  single-agent flow where `subagents` is undeclared).
- **One body source, many dialects.** Bodies are dedicated distilled
  templates — one per command, shared by all harnesses — not mechanical
  SKILL.md transforms. An adapter contributes only its identity, target
  paths, frontmatter dialect, and feature set (OpenSpec's
  `toolId`/`getFilePath`/`formatFile` shape as stdlib registry data;
  validated by tests, never by pydantic). Generated command ids use the
  `shipd-` prefix (e.g. `shipd-plan`), mirroring OpenSpec's `opsx-` prefix.
- **Install-time writes stay machine-global; repo writes go through a
  guarded verb.** `shipd install` records the harness selection and writes
  only user-global surfaces (paralleling the launcher write; it never touches
  a repository or settings file). Project-level files land via
  `shipd harness add`/`remove` `--root` — the fourth verb of the
  `statusline`/`copilot`/`vendor` family: ownership markers, idempotent
  refresh, refusal on foreign files without `--force`, no network.
- **Branding is additive.** The animated block-letter **SHIPD** wordmark
  (OpenCode-style) opens `shipd install` and appears nowhere else; ☕ remains
  the inline brand mark per the verified `project-readme`, `shipd-install`,
  and `statusline` requirements. All animation and color is TTY-gated and
  honors `NO_COLOR`; non-TTY output is plain and static.
- **`curl | sh` owns stdin, so interaction reads `/dev/tty`.** When no TTY is
  available (CI, redirected runs), `shipd install` degrades to the current
  non-interactive finish: no prompt, no selection recorded, instructions
  printed instead. `install.sh` keeps its POSIX-sh, download-nothing,
  idempotent contract.

## Design

The framework is a render pipeline from one content source through per-harness
dialects to two write surfaces:

```
command bodies ──── one feature-gated template per /s: command
      │  render(features)
      ▼
adapter registry ── 11 entries: id · display name · user-global dir ·
      │             repo-relative dir · frontmatter dialect · declared features
      ├────────────▶ shipd install        (machine-level, once, from install.sh:
      │              wordmark animation → /dev/tty multi-select → selection
      │              record + user-global command dirs where supported)
      └────────────▶ shipd harness add    (per-repo, repeatable: --root, owned,
                     [/remove]             idempotent, --force; writes
                                           .cursor/commands/, .github/prompts/,
                                           .omp/commands/, .windsurf/…, …)
```

The install chain gains one link at the end:
`curl | sh → prereq checks → claude plugin install → launcher →
exec shipd install` — everything before the new link is untouched, and
`shipd install` re-run later by hand reopens the same selection.

The decomposition follows the pipeline's seams: the wordmark is a pure
rendering module with no knowledge of harnesses; the registry is data plus
read verbs with no knowledge of file writing; the bodies are content with no
knowledge of dialects; the generation verb composes all three; the install
TUI composes the verb's user-global half with the wordmark and the
interactive flow; the docs member records the new mode. Each member is
independently testable under the stdlib-only test suite.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| shipd-wordmark | Stdlib ANSI block-letter SHIPD wordmark module: static and animated color rendering, TTY/`NO_COLOR`-gated, plain non-TTY fallback; exposed to the binary, used by the install TUI | low | low | low | low |
| harness-registry | Feature vocabulary + the 11 harness registry entries (ids, display names, user-global and repo-relative target dirs, frontmatter dialects, declared features) + `shipd harness` read verbs (`list`/`show`, `--json`); per-harness path/capability research recorded as registry data | medium | low | medium | low |
| harness-command-bodies | The distilled feature-gated body template per /s: command, the externalized fallback reference files, and the render function that composes a body for a feature set (progressive-disclosure router pattern, three-step degradation protocol) | medium | medium | high | medium |
| harness-verb | `shipd harness add`/`remove` `--root` generation verb: renders bodies through each adapter dialect into the repo-level and user-global dirs, with ownership markers, idempotent refresh, `--force`, and report-only bare mode, per the `copilot`/`vendor` family | high | high | medium | medium |
| install-tui | Interactive `shipd install` verb: wordmark animation, `/dev/tty` harness multi-select, selection record, user-global generation for selected harnesses, non-TTY degradation, and the `install.sh` wiring that execs it at the end | high | high | medium | high |
| harness-docs | README + quickstart harness mode: the selection step in the install flow, `shipd harness add` for repositories, the feature-scaling model, and the additive brand note | low | low | low | low |

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 359 | 163.1k |
| Edit | 79 | 65.1k |
| Write | 15 | 58.9k |
| (no tool) | 0 | 25.7k |
| Read | 58 | 12.5k |
| Agent | 10 | 4.6k |
| SendMessage | 5 | 4.0k |
| Monitor | 3 | 680 |
| TaskStop | 3 | 470 |
| ToolSearch | 2 | 453 |
| Skill | 1 | 159 |
| **Total** | 535 | 335.7k |
