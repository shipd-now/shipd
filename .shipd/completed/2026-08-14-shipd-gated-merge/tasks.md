# shipd-gated-merge — tasks

All remote work runs from the shipd checkout at
`/Users/mikkelbergmann/projects/shipd`, and every GitHub API call is prefixed
`GH_TOKEN="$(cat ~/.shipd-gh-token)"` — that token is the operator-supplied
mechanism and carries `admin` on `shipd-now/shipd`. Never echo, log, or write
the token's value; only ever reference it through that `$(cat ...)` form.
Report any pull request with its full clickable URL, never its number.

## 1. Preconditions

- [x] 1.1 [req: *] From `/Users/mikkelbergmann/projects/shipd`, confirm the
      credential still works and carries the needed scope:
      `GH_TOKEN="$(cat ~/.shipd-gh-token)" gh api repos/shipd-now/shipd --jq
      .permissions` must report `"admin": true`. If it does not, stop and report
      — no later task may run without it.

## 2. Repository merge settings

- [x] 2.1 [req: gate-merge-settings] Set shipd's merge settings with
      `GH_TOKEN="$(cat ~/.shipd-gh-token)" gh api -X PATCH repos/shipd-now/shipd`
      so that `allow_squash_merge=true`, `allow_merge_commit=false`,
      `allow_rebase_merge=false`, `allow_auto_merge=true`, and
      `delete_branch_on_merge=true`.
- [x] 2.2 [req: gate-merge-settings] Re-read the repository object from the API
      and confirm all five values independently of the PATCH's own response.

## 3. Record the authoring mechanism

- [x] 3.1 [req: gate-authoring-path-recorded] In
      `/Users/mikkelbergmann/projects/.shipd/wiki/queue.md`, replace the
      `- Answer: pending` line of `q-shipd-pr-authoring` with the mechanism used
      — an operator-supplied token file read per invocation into `GH_TOKEN`,
      rather than a `gh auth login` that would change shipd's own PR identity
      — and the scope it required (`admin` on the repository, needed for the
      branch-protection read and the settings PATCH). Write no token value and
      no token file contents.

## 4. Verify the gate's end state

- [x] 4.1 [P4] [req: gate-branch-protection] Read
      `GH_TOKEN="$(cat ~/.shipd-gh-token)" gh api
      repos/shipd-now/shipd/branches/main/protection` and confirm the required
      contexts are `ci` and `semantic-review`, `enforce_admins` is enabled,
      `required_conversation_resolution` is enabled, and a pull request is
      required before merging. Record `required_status_checks.strict` as
      observed; per `plan.md` it is deliberately left `false` to match shipd
      — do not change it.
- [x] 4.2 [P4] [req: gate-branch-protection] From
      `/Users/mikkelbergmann/projects/shipd`, run
      `GH_TOKEN="$(cat ~/.shipd-gh-token)" python3
      plugins/s/skills/review/scripts/review_gate.py protect` and confirm its
      printed line reports contexts `ci, semantic-review` and conversation
      resolution `required`. Re-read the protection afterwards and confirm it is
      unchanged from task 4.1's reading.
- [x] 4.3 [P4] [req: gate-stack-landed] Confirm each of the six member branches
      — `shipd-port-tool`, `shipd-engine-port`, `shipd-library-port`,
      `shipd-identity`, `shipd-brand`, `shipd-evals-port` — has a merged pull
      request (`gh pr list --repo shipd-now/shipd --state merged`), and that
      `git ls-remote --heads origin` shows none of the six still on the remote.
- [x] 4.4 [P4] [req: gate-stack-landed] Check out `main` fresh and confirm
      `plugins/s/`, `.shipd/`, `tools/port.py`, `evals/`, and
      `.github/workflows/ci.yml` are all present, and that the `ci` run for the
      latest push to `main` concluded successfully
      (`gh run list --repo shipd-now/shipd --branch main`).
- [x] 4.5 [P4] [req: gate-stack-landed] For each of the six slugs, count the
      commits on `origin/main` whose subject begins with that slug and a colon
      (`git log --format=%s origin/main`). Record the counts, confirm they match
      the gap `plan.md` describes, and confirm `git log --format='%h %p'` shows
      the member merges as merge commits — i.e. the history was not rewritten.
- [x] 4.6 [P4] [req: gate-exercise-transit] Read the exercise pull request
      (`change/locate-current-fallback`) and its head commit's combined status.
      Confirm the pull request is merged, its head branch is gone from the
      remote, and the `semantic-review` status on its head is `success` with a
      target URL pointing at the gate poster's summary comment.

## 5. Verify the push refusal

- [x] 5.1 [req: gate-branch-protection] Confirm the branch refuses a direct
      push, using a payload that would be harmless if it somehow landed: from
      `/Users/mikkelbergmann/projects/shipd`, `git fetch origin`, create a
      scratch branch at `origin/main`, add one `git commit --allow-empty`
      commit, attempt `git push origin <scratch>:main`, and confirm the remote
      rejects it — quoting the rejection message in the report. Then delete the
      scratch branch locally. If the push unexpectedly succeeds, stop
      immediately and report it as a gate failure.

## 6. Final report

- [x] 6.1 [req: gate-authoring-path-recorded] Search both repositories' tracked
      files and this change's artifacts for the credential's value and confirm
      no match. Perform the search without printing the value itself.
- [x] 6.2 [req: *] Report the five confirmed merge settings, the protection's
      required contexts and flags, the six merged member pull requests and the
      exercise pull request with their full clickable URLs, the per-slug
      `<slug>:` subject counts from task 4.5, and the quoted push rejection from
      task 5.1.
