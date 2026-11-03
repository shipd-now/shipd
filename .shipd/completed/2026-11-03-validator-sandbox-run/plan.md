# validator-sandbox-run
Status: verified
Planned-at: 3e82fbf1c963f4592a891bbb29c010ad5bb676fb
Gated-hash: e99806152e72

## Idea

Give the validator and sandbox-shaped sub-agent work one execution entry point, `sandbox-run.sh`, that applies the sandbox env by construction.

### Motivation

A validator run overwrote the user's real `~/.review-bot/config.json` and made one live `gh api` call, because one command dropped its HOME override. The sandbox exists only as spawn-message prose, so every command must carry the env by hand and a single slip reaches real user state.

### Details

- New `plugins/s/skills/build/scripts/sandbox_run.py` (stdlib core) behind a `sandbox-run.sh` bash shim.
- New `sandbox` key in `.shipd-config.json`: `fake_bin` and `env`.
- `agents/validator.md` and `agents/sub-agent.md` (plus their `harness/agents/` twins) gain a sandbox contract.
- Build passes the wrapper's absolute path in the validator and sub-agent spawn messages.

Affected capabilities: `validator-sandbox` (new), `shipd-config`, `build-subagent-handoff`, `build-spec-lifecycle`.

### Non-goals

- No PreToolUse Bash hook; enforcement is the agent contract plus the wrapper.
- No OS-level isolation (containers, `sandbox-exec`); writes inside the repo checkout stay real.
- No review-bot or autome names in shipd code; projects declare their own vars.

## Implementation

**Shape.** `sandbox-run.sh` is a three-line bash shim: `exec python3 "$(dirname "$0")/sandbox_run.py" "$@"`. All logic lives in `sandbox_run.py`, so it is stdlib-only and unit-testable. Rejected: pure bash, because reading the layered config from bash means parsing `config-show` text.

**CLI.**
- `sandbox-run.sh '<command>'`: exactly one positional argument, run as `bash -c '<command>'` inside the sandbox. Zero or two-plus positionals exit 2 with `sandbox-run: pass the command as one quoted string`. Rejected: argv passthrough, because the caller's shell expands `~` and `$HOME` to the real home before the wrapper runs.
- `sandbox-run.sh --reset`: deletes the sandbox root, prints it, exits 0.
- `sandbox-run.sh --print-root`: prints the root, creates nothing, exits 0.

**Root.** `<tmp>/shipd-sandbox/<id>`. `<tmp>` is `tempfile.gettempdir()` read before the env is rewritten. `<id>` is the first 12 hex chars of the sha256 of the repo root (`git rev-parse --show-toplevel`, falling back to the absolute cwd). The root persists across calls, so multi-step scenarios keep state. Layout: `home/`, `tmp/`, `state/`. On a create failure, print `sandbox-run: cannot create sandbox root <path>: <error>` to stderr and exit 3. If the root resolves under the real HOME, print `sandbox-run: sandbox root <path> is inside the real HOME` and exit 3.

**Banner.** The first stderr line of every run is `sandbox-run: root=<root>`.

**Env.** Start from the inherited env, then:
- Scrub: drop `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN` and `GITHUB_ENTERPRISE_TOKEN`. Also drop every var, except `PATH`, whose value holds a real-HOME occurrence not followed by the repo root (the "outside-repo home reference" below).
- Set `HOME=<root>/home`, `XDG_CONFIG_HOME=<root>/home/.config`, `XDG_STATE_HOME=<root>/home/.local/state`, `XDG_CACHE_HOME=<root>/home/.cache`, `XDG_DATA_HOME=<root>/home/.local/share`, `GH_CONFIG_DIR=<root>/home/.config/gh`, `GIT_CONFIG_GLOBAL=<root>/home/.gitconfig`, `GIT_CONFIG_NOSYSTEM=1`, `TMPDIR=<root>/tmp`, `SHIPD_SANDBOX=1`, `SHIPD_SANDBOX_ROOT=<root>`.
- Apply the `sandbox` config: each `env` entry `NAME: rel` sets `NAME=<root>/state/<rel>`, and its parent directory is created. `fake_bin` prepends `<repo-root>/<fake_bin>` to `PATH`. If `fake_bin` is declared but missing on disk, exit 3 with `sandbox-run: fake_bin <path> does not exist`.

**Leak refusal.** Before running, refuse with exit 2 when the command string holds an outside-repo home reference: an occurrence of the real HOME path (`os.path.realpath` and the literal `$HOME` value both checked) whose continuation does not begin with the repo-root path. Message: `sandbox-run: command names the real HOME outside the repo: <match>`. A bare `~` or `$HOME` inside the single-quoted string expands to the sandbox HOME in the inner bash.

**Config key.** `sandbox` joins `spec_common.RECOGNIZED_CONFIG_KEYS` and gets a `config_registry.REGISTRY` row with layer `repo`, no owner, and a `_validate_sandbox` validator. That validator accepts an object with optional members only:
- `fake_bin`: a non-empty relative path with no `..` segment.
- `env`: an object mapping names matching `^[A-Z_][A-Z0-9_]*$` to non-empty relative paths with no `..` segment.

Any other member or shape is an error. The example config documents `// sandbox`, and `docs/customise.md` gains a table row. `sandbox_run.py` reads it via `spec_common.resolve_config(repo_root)` before the env swap.

**Contract.** `validator.md` gains a `## Sandbox` section. The spawn message supplies `<SANDBOX_RUN>`. Every Bash command that runs `gh`, `git`, a project script, a test, or anything that reads or writes state goes through `bash <SANDBOX_RUN> '<command>'`. A bare Bash call is allowed only for read-only listing and reading of files (`ls`, `cat`, `grep`, `find`), and the Read and Grep tools stay direct. A raw `gh`/`git`/script call is a contract violation. Every sandboxed call starts with the wrapper path and prints the `root=` banner, so a violation shows in the transcript. The guardrail forbidding git use is kept; this section governs only how code is exercised. `sub-agent.md` gains a short paragraph: when a task exercises `gh`, git remotes or watcher scripts against fakes, run those commands through `<SANDBOX_RUN>`. Each `harness/agents/` twin gets the same body text, and a test pins body parity.

**Build.** `build/SKILL.md` adds the absolute `sandbox-run.sh` path (as `<SANDBOX_RUN>`) to the sub-agent spawn message (around line 342) and the validator spawn message (step 5, around line 528).

**Risk.** Scrubbing home-referencing vars can strip a tool path such as `VIRTUAL_ENV`. `PATH` is kept whole, so real tools still resolve; a missing var surfaces as a scenario failure, never as a leak. Real `gh` stays reachable when `fake_bin` lacks it, but runs with no token and an empty config dir, so it is unauthenticated.

## Questions and answers

### Q1: Where does the wrapper learn project fake-bin and state vars?
- **Question:** Source of a project's fake-bin dir and state env vars. Options: (a) a new `sandbox` config key plus a scrub baseline; (b) generic redirect plus scrub and a `--fake-bin` flag; (c) hardcoded review-bot and autome names. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a): a `sandbox` key with `fake_bin` and `env`, with the scrub of home-referencing vars as the baseline.
- **Queued:** q-sandbox-project-state-source

### Q2: How is the no-raw-Bash rule enforced?
- **Question:** Options: (a) agent contract plus wrapper banner, visible in the transcript; (b) also a PreToolUse Bash hook. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a): the contract and the transcript-visible banner; no hook.
- **Queued:** q-sandbox-enforcement-strength

### Q3: Does the sub-agent adopt the wrapper now?
- **Question:** Options: (a) yes, one contract paragraph; (b) validator only. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a): a one-paragraph sandbox rule in `sub-agent.md`.
- **Queued:** q-sandbox-subagent-scope

## Readiness attestation

### Problem and motivation

A prose-only sandbox let one validator command overwrite real user state and call the live GitHub API.

Evidence:

- `plugins/s/agents/validator.md:1-86` carries no sandbox rule at all.
- `build/SKILL.md:528` sends the validator only the change name, so the sandbox lived in ad hoc prose.

### Scope and non-goals

The scope covers the wrapper, the config key, the two agent contracts and the two spawn messages; hooks and OS isolation stay out.

Evidence:

- `plugins/s/hooks/hooks.json` matches only `Edit|Write`; no Bash hook is added.
- Capability `container-spike` covers OS-level isolation separately.

### Affected capabilities and files

Four capabilities and about ten files are affected.

Evidence:

- New capability `validator-sandbox`; `shipd-config`; `build-subagent-handoff` (artifact-compiled-context-handoff, base 0a94a929ac04); `build-spec-lifecycle` (adversarial-validation-gates-verified, base 8dde8af7dd1d).
- Files: `plugins/s/skills/build/scripts/{sandbox-run.sh,sandbox_run.py,config_registry.py:247,spec_common.py:407}`, `plugins/s/skills/build/references/shipd.config.example.json`, `docs/customise.md:48`, `plugins/s/agents/{validator,sub-agent}.md`, `plugins/s/harness/agents/{validator,sub-agent}.md`, `plugins/s/skills/build/SKILL.md:342,528`.
- Runnable premise: `env -u GH_TOKEN -u GITHUB_TOKEN HOME=<tmp> GH_CONFIG_DIR=<tmp>/gh gh api user` printed "To get started with GitHub CLI, please run: gh auth login", so it is unauthenticated.
- Runnable premise: `HOME=<tmp> GIT_CONFIG_GLOBAL=<tmp>/.gitconfig GIT_CONFIG_NOSYSTEM=1 git config --global user.name sbx` exited 0 and wrote only `<tmp>/.gitconfig`.
- Runnable premise: `diff` of each `plugins/s/agents/*.md` body against its `harness/agents/` twin printed nothing, so the bodies match.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Config source, enforcement strength and sub-agent scope: settled by the user, Q1 to Q3.
- Python core behind a bash shim, per-repo persistent root, and single-string command: settled by investigation (constitution stdlib rule; the tilde-expansion leak).
