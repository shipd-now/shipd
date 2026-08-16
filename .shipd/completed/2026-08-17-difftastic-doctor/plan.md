# difftastic-doctor
Status: verified

## Idea

Make a missing difftastic loud and self-healing: the `shipd doctor` preflight probes for it, `/s:doctor` offers its installer as a consented remedy, and `/s:review` tries the installer automatically before reviewing — telling the user plainly when the install fails and the review must degrade.

### Motivation

A review run without difftastic silently degrades to the structural-text engine and loses syntax-aware accuracy, yet the `shipd doctor` preflight never probes for difftastic and the review flow only offers the installer if the user thinks to ask — the very review that shipped this repo's last PR ran degraded without anyone deciding that.

### Details

- Add a `warn difft` check to the `shipd doctor` preflight, with a detail naming the review degradation and the installer remedy.
- Add the matching consent-gated remedy row to `/s:doctor`: the tiered installer `semdiff.py doctor --fix`.
- Change `/s:review`'s degradation flow: when `difft` is missing at review start, run the tiered installer automatically, re-probe, and on failure inform the user prominently and record the degradation in `could_not_verify` — then complete the review on the text engine.

Affected capabilities: `shipd-cli` (doctor-verb, modified), `shipd-doctor` (doctor-remedy-boundaries, modified), `semantic-review` (added requirement). Impact: `plugins/s/bin/shipd`, `plugins/s/skills/build/tests/test_shipd_cli.py`, `plugins/s/skills/doctor/SKILL.md`, `plugins/s/skills/review/SKILL.md`, plugin version bump.

### Non-goals

- No change to `semdiff.py` itself — its `doctor` verb and tiered `--fix` installer already exist and stay as spec'd (`doctor-provisioning`), including the invariant that network access occurs only under `--fix`.
- No hard-block of reviews: difftastic stays recommended-never-required; a review always completes, at worst on the text engine after the user has been informed.
- No change to the Copilot review workflow — `integrations/copilot/copilot-code-review.yml` already installs difftastic in its own environment.
- No auto-install anywhere outside the review entry point; `/s:doctor` remedies stay consent-gated per `doctor-remedy-boundaries`.

## Implementation

- **Probe placement and mechanics.** `bin/shipd`'s doctor gains a `check_difft` reported directly after `gh`, using stdlib `shutil.which("difft")` so the binary stays stdlib-only (constitution). Missing → `warn difft — not found — reviews degrade to the text engine; run /s:doctor or `semdiff doctor --fix``-style detail; present → `ok difft — found at <path>`. Warn, never fail: the spec'd posture is recommended-never-blocking.
- **Remedy row.** `/s:doctor`'s remedy table maps a `warn difft` to `python3 "${CLAUDE_PLUGIN_ROOT}/skills/review/scripts/semdiff.py" doctor --fix` — runnable on consent, network access stated before it runs (it is the one remedy that may download a binary). The known-checks list in the skill gains `difft`.
- **Review auto-fix gate.** `/s:review`'s Degradation section changes from offer-on-request to: at review start, when `difft` is not on PATH, run the tiered installer via `semdiff doctor --fix`, then re-probe. Success → proceed syntax-aware, no ceremony. Failure → a prominent user-visible notice naming the text-engine degradation and the manual hint (`brew install difftastic`), plus a `could_not_verify` entry in both human and `--json` output — then the review proceeds. The user's standing instruction is the say-so for this one auto-invocation; the installer's network-only-under-`--fix` invariant is preserved because the flow reaches the network solely through `--fix`.
- **Runnable premises verified.** `python3 plugins/s/skills/review/scripts/semdiff.py doctor` → `- difft — recommended, not found…`, exit 0 (the probe and hint the flow builds on); `plugins/s/bin/shipd doctor` → nine checks, no difft line, exit 0 (the gap being filled); `python3 -m unittest discover -s plugins/s/skills/build/tests` → 1446 tests OK this session (the suite the new check tests join).
- **Version bump.** `plugins/s/` changes, so `plugins/s/.claude-plugin/plugin.json` bumps `0.6.124` → `0.6.125`.

Risk: `semdiff doctor --fix` can take noticeable time (download) at review start on a cold machine; bounded by running it only when `difft` is absent, and the failure path never retries — one attempt per review, then inform and degrade.
