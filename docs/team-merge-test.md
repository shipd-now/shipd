<!-- doc-type: how-to -->

# Prove the merge rules on the test repository

GitHub, not an agent, must enforce the shipd merge rules. This guide runs
`tools/team_merge_test.py` against `mikkel-bergmann/unkannybanny` to show
GitHub blocking and then releasing one throwaway pull request, and records
what GitHub said. The driver refuses any other repository.

[Give an agent its own GitHub account](agent-identity.md) covers the second
account this run needs.

## Before you start

- You have the author's `gh` login, with the `workflow` scope.
- A second account is a write collaborator on `mikkel-bergmann/unkannybanny`
  and has accepted the invitation.
- Actions may approve pull requests on the repository
  (`can_approve_pull_request_reviews` is true). `/s:gate` offers this
  setting.
- The repository holds the `COPILOT_GITHUB_TOKEN` Actions secret.
- You have a clone of the repository with a clean `main`.

## Export the reviewer credential

1. Choose one credential for the second account:
   - `TEAM_TEST_REVIEWER_GH_TOKEN`, a token for the account.
   - `TEAM_TEST_REVIEWER_GH_CONFIG_DIR`, a `gh` config directory signed in
     as the account.
2. Export it in your own shell. The driver copies it into the reviewer
   subprocess only, never prints it, and replaces any trace of it with
   `[redacted]`.

Do not paste the credential into a file, a chat, or a command argument.

## Prepare the repository

1. In the clone, create a branch and run `shipd copilot add`. It installs the
   review gate files, including `.github/workflows/copilot-review-gate.yml`.
2. Add an explicit `merge` block to `.shipd-config.json`:

   ```json
   {"merge": {"approvals": 2, "dismiss_stale": true,
              "last_push_approval": true, "thread_resolution": true,
              "required_checks": ["ci", "semantic-review"]}}
   ```

3. Open a pull request, wait for `ci` and `semantic-review`, and merge it.
   The existing zero-approval ruleset on `main` still governs this one.

## Run the proof

1. Check the prerequisites from the clone:

   ```sh
   python3 tools/team_merge_test.py preflight --root <clone>
   ```

   Each line reads `ok <name> - ...` or `missing <name> - <fix>`. Any
   `missing` line exits 3. Fix it and run again. `--only user` checks the
   accounts and settings; `--only repo` checks the prepared repository.

2. Apply the ruleset and read it back from GitHub:

   ```sh
   python3 tools/team_merge_test.py apply --root <clone>
   ```

   The driver runs `shipd gate rules apply`, then checks two approvals,
   dismissal on push, last-push approval, thread resolution, the `ci` and
   `semantic-review` checks, and no bypass actors. Any `FAIL` line exits 1.

3. Run the scenario:

   ```sh
   python3 tools/team_merge_test.py run --root <clone> --out <dir>
   ```

   The driver opens one throwaway pull request and walks through six steps:

   - (a) One approval, from the CI bot, leaves the merge call refused with
     HTTP 405 and the state `BLOCKED`.
   - (c) GitHub refuses the author's own approval, and `shipd room whoami` as the
     author exits 1. The reviewer's `whoami` exits 0 and the second approval
     makes the state `CLEAN`.
   - (b) A push by the author that changes the diff dismisses the reviewer's
     review. The merge call stays refused while the bot alone re-approves.
     GitHub keeps approvals across an empty commit, so the driver pushes a
     real edit.
   - (d) With no unresolved threads, the driver arms auto-merge while only one
     approval stands, then the reviewer approves the head. The pull request
     reaches `MERGED` without a manual merge call.
   - (e) `shipd doctor` shows no drift for `protection`, `merge-rules`, and
     `actions-approve`, and `shipd gate rules` shows no `differs` line.

   Each assertion lands in `<dir>/evidence.json` as `id`, `claim`,
   `observed`, `ok`, and `at`. The run stops at the first failed assertion
   and leaves the pull request open for you to inspect.

4. Render the evidence as a retro record:

   ```sh
   python3 tools/team_merge_test.py report --evidence <dir>/evidence.json \
     --output docs/retros/<run-date>-team-merge-test.md
   ```

## Check the result

1. Confirm the run exited 0 and `evidence.json` holds `"result": "pass"`.
2. Open the pull request URL in the retro record. GitHub lists two approvals
   from logins other than the author and the state `Merged`.
3. Search the record for `ghp_` and `github_pat_`. Neither appears.

## If something fails

- A `missing` line from `preflight`: follow its fix text, then rerun.
- A `FAIL` from `apply`: the live ruleset differs from the `merge` block.
  Read `shipd gate rules` for the member that differs.
- A failed step in `run`: the pull request stays open. Read the last record
  in `evidence.json`; it names the claim and what GitHub returned. After a
  stop at `b-push-dismisses`, `run --resume --out <dir>` continues on the same
  pull request and keeps the earlier records. It relabels the failed record
  as `b-empty-push-keeps-approvals` only when the GitHub compare API shows no
  changed file between the record's old and new head. A failed push that
  changed files stops the run: it exits 1 and the record stays failed.
