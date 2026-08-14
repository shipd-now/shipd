## 1. Oracle search ladder

- [x] 1.1 [req: oracle-agent-contract] In `plugins/s/agents/oracle.md`, under
      "## The search ladder (binding order)", add a new **first** rung —
      "Personal memory — the user's private store (first)" — before the current
      Job wiki rung, and renumber the existing rungs (Job wiki → 2, Base wiki →
      3, repo surfaces → 4). The new rung SHALL direct reading the personal
      store via `cat wiki index --personal`, `cat wiki <slug> --personal`, and
      read-only grep under the directory `wiki-show --personal` prints (all with
      `--root` at the asking repo), and SHALL state that an absent personal
      store (`wiki-show --personal` reports no store) is skipped without error,
      mirroring an `(absent)` base rung.
- [x] 1.2 [req: oracle-agent-contract] In `plugins/s/agents/oracle.md`, update
      the ladder's intro line (currently "Resolve the answer job-wiki-first,
      then the base wiki, then widen…") and the "take the first durable
      position" line so both describe the personal-then-job-then-base-then-repo
      order, keeping the first-position short-circuit rule.

## 2. Citation marker

- [x] 2.1 [req: oracle-cited-answers] In `plugins/s/agents/oracle.md`'s
      `ANSWER` section, add the personal-store citation marker alongside the
      existing base marker: a page read from the personal store is cited
      `Cited: [[slug]] (personal)`. Add a `(personal)` line to the worked
      `ANSWER` example block so both markers appear.

## 3. Packaging

- [x] 3.1 [req: oracle-agent-contract] Bump the plugin version to `0.6.22` in
      `plugins/s/.claude-plugin/plugin.json` (this change touches
      `plugins/s/`), then run the engine unit suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      confirm it still passes (no engine code changed, so it must remain green).
