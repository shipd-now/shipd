## 1. The guide

- [x] 1.1 [req: copilot-review-guide] Write `docs/copilot-review.md` with the
      sections and content the `copilot-review-guide` requirement fixes, in
      task order: what/prerequisites, install (`shipd copilot add`, the three
      managed files, commit + push, head-branch rule), enablement (per-PR
      reviewer request and branch ruleset), maintenance (bare-report states
      `installed`/`stale`/`foreign`/`absent`, re-`add` upgrade, `remove`,
      `--force`), and scope/limits (advisory beside `semantic-review`, no
      repo-side model selection, relevance-driven pickup, optional
      difftastic/ripgrep with text-engine degradation). Ground every claim in
      `.shipd/verified/shipd-cli/spec.md` (`copilot-verb`),
      `.shipd/verified/copilot-review-skill/spec.md`,
      `.shipd/research/copilot-code-review/report.md`, and the real output of
      `plugins/s/bin/shipd copilot` against a scratch directory; follow the
      prose style of `docs/quickstart.md`.
- [x] 1.2 [req: copilot-review-guide] Verify the guide against reality: run
      `plugins/s/bin/shipd copilot` (bare) and `add`/`remove` against a temp
      directory and confirm every command, file path, report state word, and
      output line quoted in the guide matches the binary's actual behavior;
      confirm the GitHub-side claims (head-branch reading, ruleset
      enablement, relevance-driven pickup) match the research report's cited
      statements. Fix any mismatch in the guide.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 41 | 15.3k |
| Write | 4 | 8.8k |
| (no tool) | 0 | 3.9k |
| Read | 8 | 1.3k |
| Edit | 3 | 1.1k |
| Agent | 2 | 869 |
| **Total** | 58 | 31.2k |
