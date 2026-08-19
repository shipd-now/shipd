## 1. GitHub-side checks in the doctor verb

- [x] 1.1 [req: doctor-github-checks] In
      `plugins/s/skills/build/tests/test_shipd_cli.py`, add failing tests for
      the three new checks with injected `gh` runners (no network): no
      GitHub remote → all three `ok` skipped; protection probe 404 →
      `warn protection` naming the unprotected default branch; contexts
      without `semantic-review` → `warn protection` naming the missing
      context; contexts with `semantic-review` → `ok`; 403 + branches-listing
      `protected: true` → `ok` with the unverifiable note; 403 + `protected:
      false` → `warn`; `allow_auto_merge: false` → `warn automerge` (config
      undeclared) and `ok` with the draft note (`pr-mode: draft` declared);
      gate workflow present + secrets listing without `COPILOT_GITHUB_TOKEN`
      → `warn copilot-secret` naming the fail-open poll fallback; secrets
      listing with it → `ok`; no gate workflow file → `ok` skipped; secrets
      listing denied → `ok` unverifiable. Also assert admin-missing warn
      details state the lacking admin permission, and that the three lines
      print after `statusline`. Run them and observe them fail.
- [x] 1.2 [req: doctor-github-checks] In `plugins/s/bin/shipd`, implement the
      checks per the plan's Implementation section: an injectable
      `_gh_api(path)` runner and a once-resolved repository context
      (`gh repo view --json nameWithOwner`, then `gh api repos/<nwo>` for
      default branch / `allow_auto_merge` / `permissions.admin`), then
      `check_protection`, `check_automerge` (via `sc.resolve_pr_mode`), and
      `check_copilot_secret` (gated on
      `.github/workflows/copilot-review-gate.yml` existing at the root).
      Append the three to `default_checks` after `check_statusline`, degrade
      every probe failure to `ok` with a skip/unverifiable note, and update
      `_gh_auth_status`'s "the one subprocess in the doctor path" comment to
      name the new probes.
- [x] 1.3 [req: doctor-github-checks] Confirm the new tests pass and run the
      full `plugins/s/skills/build/tests/` suite (no `textual`/`pydantic`
      installs) to confirm nothing regressed.

## 2. Consent-gated remedies in /s:doctor

- [x] 2.1 [req: doctor-remedy-boundaries] In
      `plugins/s/skills/doctor/SKILL.md`: add `protection`, `automerge`, and
      `copilot-secret` to step 2's check-name list; add three remedy-table
      rows — unprotected branch → the whole-protection PUT requiring
      `semantic-review` (minimal body per the delta), missing context on a
      protected branch → the contexts-append POST (never the PUT), auto-merge
      disabled → the `allow_auto_merge=true` PATCH — each stating the exact
      mutation in its consent option and demoted to report-only when the
      finding's detail states admin is lacking; and add the `copilot-secret`
      hand-off row (relay the minimal-PAT steps from `docs/copilot-review.md`,
      hand the user `! gh secret set COPILOT_GITHUB_TOKEN`, never run it).

## 3. Docs and version

- [x] 3.1 [req: *] In `docs/copilot-review.md`, add a short "Preflight the
      GitHub settings" section after the merge-gate section: `shipd doctor`
      reports `protection`/`automerge`/`copilot-secret`, and `/s:doctor`
      applies the consent-gated `gh api` fixes where the token has admin.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` from 0.6.139
      to 0.6.140.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 86 | 37.7k |
| Edit | 21 | 32.9k |
| (no tool) | 0 | 7.7k |
| Agent | 3 | 2.1k |
| Read | 18 | 2.1k |
| **Total** | 128 | 82.6k |
