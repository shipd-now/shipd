# base-hash-verb
Status: active

## Idea

Replace the emission reference's unrunnable inline base-hash snippet with a `base-hash` verb on the status CLI, and document the one-line call instead.

### Motivation

`plugins/s/skills/plan/references/emission.md:310` documents the only way to compute a `base:` hash as a snippet that pipes the spec and heredocs the program into the same stdin; run verbatim it exits 1 with a `SyntaxError`. Every plan touching a MODIFIED or REMOVED requirement walks that path, so each one has to improvise a workaround.

### Details

- Add `spec_status.py base-hash <capability> <requirement-id>`, printing the master requirement's content hash.
- Rewrite the emission reference's recipe as a single call to that verb.
- Guard the reference by executing the command it documents, so it can never drift back to something unrunnable.

Affected capabilities: `spec-status` (new requirement), `shipd-plan` (new requirement). Impact: `plugins/s/skills/build/scripts/spec_status.py`, `plugins/s/skills/plan/references/emission.md`, `plugins/s/skills/build/tests/test_spec_status.py`, `plugins/s/skills/build/tests/test_prompt_notation.py`, and the plugin version bump.

### Non-goals

- No change to how hashes are computed. The verb reuses the engine's existing primitives verbatim, so the merge check and the planner can never disagree.
- No change to the delta grammar, to `base:`'s meaning, or to the take-newer merge behavior on a stale base.
- No new `shipd` binary verb — this is an internal engine verb, like `check-base` and `config-show`.
- No sweep of other documented commands across the skill prose; this change fixes the one recipe it can prove broken.

## Implementation

- **An engine verb, not a corrected snippet.** `spec-status` already gives every verb its own requirement (`config-show-verb`, `pipeline-show-verb`, `workspace-init-verb`), and `check-base` is the direct precedent: a mechanical verb added because a flow needed it, reusing `spec_merge.master_path` for master resolution and `sc.content_hash` for the hash — the same two primitives this verb needs. A one-line documented call also cannot be mistyped the way a twelve-line snippet can. Rejected: fixing the snippet in place (a temp file, or having it shell out to `cat verified` itself) — it works, but leaves every planner retyping unrunnable-by-construction shell, and nothing can test it.
- **Both deltas are ADDED, so neither needs a `base:` hash.** The change that fixes base-hash computation therefore never has to perform the broken procedure to ship itself.
- **Verb contract.** `base-hash <capability> <requirement-id>` prints the hash and exits zero. An unknown capability, or an id absent from that capability's master, is a single `Error: <reason>` line on stderr with a non-zero exit, per `verified/cli-conventions`; a missing argument is a usage error exiting 2. It is strictly read-only.
- **Reuse the merge engine's primitives, exactly as `check-base` does.** `cmd_check_base` (`spec_status.py:1228`) resolves masters through `spec_merge.master_path` and hashes through `sc.content_hash`, so the gate and the merge can never disagree. The new verb calls the same two functions for the same reason: a planner's `base:` must be byte-identical to what `spec_merge` will later compare against.
- **The reference test executes, it does not pattern-match.** `test_prompt_notation.py` already scans `skills/**/*.md`, so the guard lands there: extract the command the reference documents, run it against a real capability and requirement id, and assert its output equals `sc.content_hash` for that requirement. A test that merely grepped for the verb's name would pass on a command that still could not run — which is the failure being fixed.
- **Version bump.** Everything lands under `plugins/s/`, so `plugins/s/.claude-plugin/plugin.json` goes `0.6.208` to `0.6.209`.

Risk: the verb's output drifting from `spec_merge`'s expectation. Guarded by both calling `sc.content_hash`, and by the reference test comparing the verb's output against that function directly.
