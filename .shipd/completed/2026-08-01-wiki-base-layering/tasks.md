## 1. Engine — wiki_base resolution and surfacing

- [x] 1.1 [req: wiki-base-key] In `plugins/s/skills/build/tests/test_spec_common.py`,
      add tests for `wiki_base_dir(ws_root)`: a config layer declaring
      `wiki_base` with a `~`-prefixed path resolves to the expanded absolute
      path; no layer declaring it returns `None`; an empty string, a
      non-string, and a relative value each raise `ConfigError` naming
      `wiki_base`. Run the tests and observe them fail — the helper does not
      exist yet.
- [x] 1.2 [req: wiki-base-key] In
      `plugins/s/skills/build/scripts/spec_common.py`, add
      `wiki_base_dir(ws_root)` beside `wiki_dir`: resolve the layered config
      from `ws_root`, return `None` when `wiki_base` is undeclared, otherwise
      require a non-empty string, apply `os.path.expanduser`, and require the
      expanded value to be absolute — raising `ConfigError` naming
      `wiki_base` on any violation. Confirm the 1.1 tests pass.
- [x] 1.3 [req: wiki-status-verbs] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add `wiki-show`
      tests: a declared base whose directory exists prints
      `base: <path> (present)`; a declared but missing directory prints
      `base: <path> (absent)`; no declared key prints `base: none`; a base
      resolving to the store's own directory prints `base: none`; a malformed
      value exits non-zero naming `wiki_base`. Observe them fail.
- [x] 1.4 [req: wiki-status-verbs] In
      `plugins/s/skills/build/scripts/spec_status.py` `cmd_wiki_show`, print
      the `base:` line after the `wiki:` line using `sc.wiki_base_dir(ws_root)`,
      comparing realpaths against the store directory for the self-reference
      case and letting a `ConfigError` surface as the verb's error exit.
      Confirm the 1.3 tests pass.

## 2. Oracle — layered read ladder

- [x] 2.1 [req: oracle-agent-contract, oracle-cited-answers, oracle-insufficient-queue]
      In `plugins/s/agents/oracle.md`: extend the search ladder to job wiki →
      base wiki → repo surfaces — the base rung runs the same wiki verbs and
      read-only grep with `--root` at the base store path printed on
      `wiki-show`'s `base:` line, and is skipped on `base: none` or
      `(absent)`; mark base-page citations `Cited: [[slug]] (base)`; state
      that `wiki-queue-add`/`wiki-init` always target the asking workspace's
      own store, never the read-only base; and in the repo-surface rung, read
      `workspace-show` and consult a declared `focus` project first via
      `project-show`.

## 3. Teach — base-aware scan and promotion

- [x] 3.1 [req: teach-distill-scan] In `plugins/s/skills/teach/SKILL.md`
      step 2: after reading the job wiki index, when `wiki-show` reports a
      present base store, read the base index (and candidate pages) with the
      same engine reads rooted at the base store path, treat base-covered
      subjects as covered (never stage a job-store duplicate), and prefer a
      declared `focus` project's surfaces first in the scan order (read the
      focus from `workspace-show`).
- [x] 3.2 [req: teach-promote-to-base, teach-gap-interview] In
      `plugins/s/skills/teach/SKILL.md` steps 3–6: classify each distilled
      page and drained answer job-scoped (default) or job-independent; offer
      promotion of job-independent items batched into the run's single
      question round (a round opens for promotion offers even when the scan
      surfaced no gaps or contradictions); install accepted promotions through a second
      staged `spec_emit.py wiki --from <staging> --root <base-store-path>`
      carrying the base's own full `index.md` and dated `log.md` entry;
      forbid `[[wikilink]]`s to pages that live only in the other store; and
      when no base is declared or present, land everything in the job store
      with no promotion offered.

## 4. Ship

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version from
      0.6.18 to 0.6.19.
- [x] 4.2 [req: *] Run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` from the
      repo root and confirm the whole suite passes.
