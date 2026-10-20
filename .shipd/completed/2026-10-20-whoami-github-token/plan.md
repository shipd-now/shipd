# whoami-github-token

Status: ready
Theme: developer-experience
Planned-at: 73156d3ce5cd7c38ac953d31cd0771c4a89ffd93
Gated-hash: dc9b80ae15ce

## Idea

The credential source that "shipd room whoami" and the "room run" start line report follows the same environment precedence the "gh" CLI uses, including GITHUB_TOKEN and the enterprise token variables.

### Motivation

An agent running in GitHub Actions or another CI job with only GITHUB_TOKEN set is told its source is "gh-login", which is false, so whoever checks the reviewer's identity before an approval reads a wrong account story. The reported name is the one signal the room gives about which account will act, so it has to match what "gh" actually does.

### Details

- `_credential_source` in `plugins/s/skills/room/scripts/room.py` takes the target host and walks gh's own precedence. On github.com and on a "ghe.com" subdomain the order is GH_TOKEN, GITHUB_TOKEN, GH_CONFIG_DIR, then "gh-login". On any other host (a GitHub Enterprise Server) the order is GH_ENTERPRISE_TOKEN, GITHUB_ENTERPRISE_TOKEN, GH_CONFIG_DIR, then "gh-login".
- A new helper names the room's host: the host of a pull request URL when one is given, else the GH_HOST environment variable, else "github.com".
- "whoami" and the "room run" start line in `plugins/s/skills/room/scripts/room_run.py` pass that host.
- The source list is updated in `docs/agent-identity.md`, `plugins/s/harness/references/room.md`, and the verified requirement.
- `plugins/s/.claude-plugin/plugin.json` moves up one patch.

Affected capability: `room-acting-account` (requirement "room-whoami-verb" modified). No other caller reasons about the credential: the room-wake workflow binds GH_TOKEN explicitly inside an "env -i" call and never reads the source name.

### Non-goals

- No change to which credential "gh" uses; the room still passes no env override.
- No reading of a host from GH_REPO or the git remote; the URL and GH_HOST are enough for the source line.
- No token value is ever read beyond a truthiness check, printed, or logged.

## Implementation

- Signature: "_credential_source(environ, host="github.com")" returns one of the six names. "Set" means a non-empty value, as today.
- Enterprise test: a host is an Enterprise Server host when, lowercased, it is neither "github.com" nor ends with ".ghe.com". This mirrors "gh help environment", which says GH_TOKEN and GITHUB_TOKEN serve "github.com or a subdomain of ghe.com" and the enterprise pair serves a GitHub Enterprise Server host. Rejected: always reporting the enterprise pair, which would name a variable gh ignores on github.com.
- On an Enterprise Server host GH_TOKEN and GITHUB_TOKEN are skipped, since gh does not use them there. Rejected: ignoring enterprise hosts entirely; the room's URL pattern accepts any host, so an enterprise room is reachable and would be misreported.
- New helper "_room_host(pr, environ)" in `room.py`: when "pr" matches "^https?://([^/]+)/", return that host; else return GH_HOST when set; else "github.com". It reads no GitHub API and runs no "gh" call.
- "cmd_whoami" calls "_credential_source(os.environ, _room_host(opts.pr, os.environ))"; `room_run.py` does the same with its "opts.pr" for the "acting as" stderr line.
- Docstrings in `room.py` (the function and the module verb list) name the full precedence.
- Tests in `plugins/s/skills/room/tests/test_room.py`: "WhoamiTest" clears all five variables plus GH_HOST from the inherited environment; "test_source_follows_the_environment" gains GITHUB_TOKEN-only, GH_TOKEN-over-GITHUB_TOKEN, and GITHUB_TOKEN-over-GH_CONFIG_DIR cases; a new test drives an enterprise URL ("https://ghe.example.com/o/r/pull/7") where GH_ENTERPRISE_TOKEN wins, GITHUB_ENTERPRISE_TOKEN is next, GH_TOKEN alone falls through to "gh-login", and asserts no token value appears in output. A test in `plugins/s/skills/room/tests/test_room_run.py` asserts the start line names GITHUB_TOKEN when only it is set.
- Risk: a test process inheriting a real GITHUB_TOKEN from CI would change the expected source. Guard: every source test clears all six variables before setting its own.

## Readiness attestation

### Problem and motivation

With only GITHUB_TOKEN set, "whoami" reports "gh-login" while gh actually authenticates with GITHUB_TOKEN.

Evidence:

- `plugins/s/skills/room/scripts/room.py:523-531` checks only GH_TOKEN and GH_CONFIG_DIR.
- "gh help environment" (run locally) prints: GH_TOKEN, GITHUB_TOKEN "(in order of precedence): an authentication token that will be used when a command targets either github.com or a subdomain of ghe.com", and GH_ENTERPRISE_TOKEN, GITHUB_ENTERPRISE_TOKEN for "a GitHub Enterprise Server host".

### Scope and non-goals

The source function, its two callers, their tests, two docs, the verified requirement, and the version.

Evidence:

- Callers found by grepping `plugins/s` for "credential_source": `room.py:682` and `room_run.py:265` only.
- `plugins/s/integrations/copilot/room-wake.yml:115` passes GH_TOKEN through "env -i" and never prints a source, so it is out of scope.

### Affected capabilities and files

One capability, "room-acting-account", requirement "room-whoami-verb" (base e1dfb1d8e276 from "spec_status.py base-hash room-acting-account room-whoami-verb").

Evidence:

- Files: `plugins/s/skills/room/scripts/room.py`, `plugins/s/skills/room/scripts/room_run.py`, `plugins/s/skills/room/tests/test_room.py`, `plugins/s/skills/room/tests/test_room_run.py`, `plugins/s/harness/references/room.md`, `docs/agent-identity.md`, `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: "gh help environment" exit 0 with the precedence quoted above.

### No open task-shaping decision

Every decision is settled under the user's pre-approved recommended defaults.

Evidence:

- Enterprise handling: report the enterprise pair only for a non-github.com, non-ghe.com host, per the brief's default.
- Host source: the PR URL, then GH_HOST, then github.com.
