## 1. Consult personal memories during investigation

- [x] 1.1 [req: memory-consultation] In `plugins/s/skills/plan/SKILL.md`, add a
      "Consult personal memories" step to the Flow's investigation stage: read the
      personal store via `spec_status.py wiki-show --personal` then `cat wiki index
      --personal`, read-only grep the store's `wiki/` dir for `memory-*` pages
      matching the change's subject terms, read each match with `cat wiki <slug>
      --personal`, and apply relevant memories to plan decisions and to the plan's
      output/expression (diagram style, tone). State that an absent store or no
      relevant page is skipped silently and never blocks planning, and that this is
      a direct read spawning no `s:oracle` — so the investigation turn stays
      oracle-free.
- [x] 1.2 [req: memory-consultation] In `plugins/s/skills/plan/SKILL.md`, require
      reporting each applied memory in user-visible text (the findings digest or
      status text) with its source slug, and state that a contradicting typed user
      reply overrides the applied memory — the same authority contract as
      oracle-settled decisions.
- [x] 1.3 [req: memory-consultation] In
      `plugins/s/skills/plan/references/readiness.md`, add the personal-memory read
      to the read → ask-mikk → human ladder as part of the "read" rung, noting it
      precedes the ask-mikk oracle rung.

## 2. Ship the plugin change

- [x] 2.1 [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.28` to `0.6.29` (any change
      under `plugins/s/` requires a version bump so the cache snapshot refreshes).
- [x] 2.2 [req: *] Run the plan evals locally from the repo root (`python3
      evals/run.py --case plan-csv-export` and `--case plan-new-capability`) and
      confirm each still produces exactly one lint-clean change promoted to `ready`;
      record the outcome. Evals are a local/manual gate — they cost model spend and
      are not part of `ci`.
