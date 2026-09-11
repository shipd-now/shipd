<!-- doc-type: reference -->

# Copilot review reference

[Install the Copilot review gate](copilot-review.md) is the how-to. This page
lists what the gate installs and how it decides.

## The managed files

`shipd copilot add` writes these four files and touches nothing else — no
network call, no `gh`, no other path.

| File | Role |
| --- | --- |
| `.github/skills/code-review/SKILL.md` | The instructions Copilot loads: what to run, how to order the work, the severity rubric, and the verdict rule. GitHub recommends the `code-review` directory name, which makes Copilot read the skill. |
| `.github/skills/code-review/scripts/semdiff.py` | The review engine, byte-identical to the one `/s:review` runs. Stdlib-only Python 3, and read-only. |
| `.github/workflows/copilot-code-review.yml` | The environment workflow for GitHub's review runner. It installs `difft` and `ripgrep`. |
| `.github/workflows/copilot-review-gate.yml` | The gate workflow. It posts the `semantic-review` commit status. |

## The two reviewer modes

The gate posts the `semantic-review` commit status — the same context
`/s:review`'s poster (`review_gate.py post`) sets. One repository secret
decides which mode a run takes.

| | CLI reviewer | Poll fallback |
| --- | --- | --- |
| Selected by | a `COPILOT_GITHUB_TOKEN` secret | no secret |
| Who reviews | headless GitHub Copilot CLI, in the gate's own job | GitHub's Copilot code review |
| Runs the shipd engine | **yes** | no — its bash tool is disabled |
| Verdict marker | the reviewer writes it | never written today |
| The status you get | strict: `fix-required` really blocks | fail-open in practice |
| Private repositories | works | the skill never loads |
| What it costs | Copilot AI credits per review | runner minutes spent waiting |

Whichever mode runs, the gate posts `semantic-review` = `pending` on the head
commit **first**, before it checks anything out. So an older commit's review
never counts for a newer one, and a later failure leaves the check `pending`.

### The CLI reviewer mode

On every pull request opened, updated, or reopened, the gate's job:

1. Posts `semantic-review` = `pending` on the head commit.
2. Checks that commit out with the full history the engine's diff needs.
3. Installs `difft`, `ripgrep`, and `@github/copilot` at a pinned version.
4. Materializes the reviewer's instructions from the base ref, with
   `git show origin/<base>:.github/skills/code-review/SKILL.md`.
5. Runs the CLI under a 10-minute timeout, in a step holding the reviewer
   secret and no other credential.
6. Classifies the output's last non-empty line in a separate step, and posts
   the resulting status.
7. Posts the review text as a pull-request comment, whatever the verdict.

- **The version pin is deliberate.** An unpinned install would let the CLI
  vendor change what the gate runs. Upgrading bumps that line in the template.
- **The base-ref pin has one fallback.** Where the base tree carries no
  `SKILL.md`, the job uses the reviewed commit's copy and logs that. Any other
  read failure fails the step, so `pending` stands.
- **A failed or timed-out run leaves `pending`.** The job discards the partial
  output and posts nothing; `review_gate.py post` is the manual out.
- **Private repositories work.** This review runs in the repository's own
  Actions job with the workflow's token, so the checkout below never arises.
- **What it costs.** Copilot AI credits per review, against the token owner's
  allowance — around ten credits for a small change. The concurrency group
  cancels the run a new push supersedes, so one push gets one review.

### The poll fallback mode

With no secret, the gate waits for GitHub's own Copilot code review of the head
commit, then classifies what that review's body says.

- **Why it polls.** Copilot submits its review with a workflow-scoped token,
  and GitHub starts no workflow run from an event such a token raises. So a
  Copilot-authored review triggers no `pull_request_review` run at all. The
  `pull_request` run reliably exists, so that run polls the reviews API. The
  gate keeps the review-event path too, for any submission GitHub routes.
- **The guarantee today is fail-open.** GitHub's review runs with its bash tool
  disabled. The shipd engine never executes there, and the reviewer never
  writes the verdict marker. A poll-mode `success` therefore means *"Copilot
  reviewed this commit; no verdict marker was parsed"*. The mode costs nothing
  and surfaces Copilot's findings, but it gates nothing semantically.
- **The poll's bounds.** The poll runs every 20 seconds for at most 15
  minutes. Each cycle re-reads the pull request's head. Once a new push moves
  it, the poll exits and that push's own run owns the gate.
- **A timeout invents nothing.** Where the window elapses with no Copilot
  review of that commit, the gate leaves the status `pending` and posts nothing
  further. The same holds when a new push cancels the poll.
- **What it costs.** Waiting occupies a runner — up to 15 runner-minutes per
  update, typically two or three. A private repository pays for those minutes.

### The verdict, in both modes

The skill instructs the reviewer to write a machine-readable marker as its last
line. The gate reads only that line: it takes the last non-empty line,
tolerates surrounding whitespace, and compares it for equality.

| The reviewed text's last non-empty line | Status posted |
| --- | --- |
| `<!-- shipd-verdict: fix-required -->` | `failure` — the merge is blocked. |
| `<!-- shipd-verdict: ship-it -->` | `success`. |
| *anything else* | `success`, described as *no verdict marker was parsed* — unless the repository turned [strictness](#strictness-shipd_gate_fail_open) on, which leaves the check `pending`. |

**Only the last line decides.** A review that describes the markers mentions
both mid-text, and the pull request installing this skill draws that review.

In poll mode the gate acts only on a review by
`copilot-pull-request-reviewer[bot]` whose `commit_id` is the current head.
That holds on the poll and on the review event alike.

### Strictness: `SHIPD_GATE_FAIL_OPEN`

Some repositories rule the opposite: a review that produced no verdict must
never green the required check. That is one repository Actions variable, which
the gate reads at classification time.

```bash
gh variable set SHIPD_GATE_FAIL_OPEN --body false
```

| `SHIPD_GATE_FAIL_OPEN` | A last line matching neither marker |
| --- | --- |
| unset (**the default**), or any value but `false` | `success`, described as *no verdict marker was parsed* — fail-open. |
| `false` | The gate posts nothing. The `pending` from the run's first step stands, and the run logs that it parsed no verdict. |

Strict mode changes only that case, on every classify path: the CLI reviewer's
output, a polled review, a review event. A real verdict still decides.

- **The manual out.** A strict repository merges a `pending` pull request from
  a session: `/s:review`, then `review_gate.py post` by hand.
- **Pair the knob with the reviewer token.** On the poll fallback no reviewer
  writes the marker, so `false` stalls every reviewed pull request. Configure
  the reviewer token first, then turn the knob.
- **Set a variable, never the workflow.** `shipd copilot add` reinstalls that
  file from the template and reverts a local edit.

### The trust boundary

The CLI reviewer runs an LLM agent, with its tools enabled, over content the
pull request carries.

**The baseline is GitHub's.** On a same-repository pull request, GitHub already
runs the branch's own copy of every workflow file, with the repository's
secrets. Anyone who can push a branch already has that reach. This workflow
introduces no new class of actor.

**The residual risk is content, not push access.** The reviewer reads text the
change carries: a diff, a commit message, an added file. A change can try to
talk it into an unearned `ship-it`, and no LLM reviewer is immune to such
steering. The gate bounds that risk rather than eliminating it:

- **The reviewer holds no credential but its own.** The CLI step's environment
  binds `COPILOT_GITHUB_TOKEN` and nothing else. The workflow's `github.token`
  lives only in the next step, which classifies and posts. A steered reviewer
  can spend credits and write a misleading body, but it cannot post the status
  or push.
- **The posting step inherits nothing from the reviewer.** A step can hand
  later steps a `$GITHUB_PATH` entry and `$GITHUB_ENV` variables. A shimmed
  `gh` would run the reviewer's own program with `github.token`, and an
  injected `SHIPD_GATE_FAIL_OPEN=true` would green a strict repository. So the
  posting step invokes `gh` by the hardcoded absolute path `/usr/bin/gh` —
  never a `PATH` lookup, never an overridable default. It re-binds the
  strictness knob in its own step-level `env:` from the `vars` context, which
  the runner evaluates and no earlier step can write.
- **That split is not a wall.** A GitHub-hosted runner gives the job
  passwordless `sudo`, so a fully steered agent could overwrite `/usr/bin/gh`
  itself. The split removes the easy routes; the floor under it is the token's
  minimality.
- **The instructions come from the base ref.** The gate reviews a change that
  edits `SKILL.md` under the rules that change asks to replace. Only a merge
  into the base moves that contract.
- **The template pins the CLI version.** The reviewer's behaviour changes when
  this template changes, not when the vendor ships.
- **The workflow decides the verdict.** The reviewer writes text; the posting
  step applies this workflow's own rules to that text's last line.
- **The session flow stays the high-assurance path.** `/s:review` plus
  `review_gate.py post` keeps a human in the loop, with your credential.

### Tokens, permissions, and the session flow

The workflow does its repository work with its own `github.token`:
`statuses: write` to post the status, `pull-requests: write` to poll and
comment. The only secret it ever reads is the optional `COPILOT_GITHUB_TOKEN`,
whose value reaches nothing but the Copilot CLI's environment.

- **Coexisting with the session flow.** `/s:review` plus `review_gate.py post`
  writes the same `semantic-review` context on the same commit. Neither poster
  excludes the other, and the newest post on a commit wins.
- **Limit: pull requests from forks.** GitHub gives a fork pull request's
  workflow a read-only token. The gate therefore posts no status there, in
  either mode, and the check stays unreported. Same-repository branches behave
  normally; on a fork, post the status from a session.
- **No bootstrap step.** The gate gates the very pull request that installs it;
  an earlier "bootstrap" limit in this guide proved wrong under dogfooding.

### Private repositories, on the poll mode

GitHub runs its Copilot review in a dynamic Actions run that checks the
repository out for itself. On a private repository that checkout has failed in
practice (`repository not found`). Nothing under `.github/skills` is then on
disk. The skill never loads, the review carries no verdict marker, and the
strictness knob classifies it.

The setup workflow is fail-soft about that. `copilot-code-review.yml` checks
the repository out `continue-on-error`, and installs `difft` and `ripgrep` only
where the checkout succeeded. The job completes with the installs skipped,
which is what GitHub's PR-visible `ccr-setup-step-failure` notice keys on. The
limit belongs to the poll fallback alone, so open that review run's log once
and confirm its checkout succeeded.

## Report states and `--force`

`shipd copilot`, run bare, reports and changes nothing. Each managed file
reports one of four states.

| State | Meaning |
| --- | --- |
| `installed` | This shipd version wrote it — the marker matches, and `semdiff.py` is byte-identical to the plugin's engine. |
| `stale` | An older shipd version wrote it, or `semdiff.py` has drifted from the plugin's copy. |
| `foreign` | The file exists and carries no `shipd-copilot` ownership marker. |
| `absent` | Not installed. |

A marker line decides ownership: `<!-- shipd-copilot v… -->` in `SKILL.md`, and
`# shipd-copilot v…` in each workflow. The installed `semdiff.py` carries no
marker, and counts as owned exactly when the `SKILL.md` beside it does.

Where a managed path is `foreign`, both `add` and `remove` refuse, name the
file, and change nothing. Once you accept losing a file your team wrote by
hand, `--force` overrides:

```bash
shipd copilot add --force        # replace the foreign file with the template
shipd copilot remove --force     # delete it along with the managed files
```

## Scope and limits

- **The gate is the workflow's, not Copilot's.** Nothing in Copilot code review
  sets a third-party commit status; a review only posts a review. Drop
  `copilot-review-gate.yml` and the Copilot run is advisory again.
- **No repository-side model selection.** The Copilot code-review surface
  exposes no option to pin which model the review runs on.
- **Skill pickup is relevance-driven.** GitHub loads skills under
  `.github/skills` when they are relevant to the review. The `code-review` name
  is GitHub's recommendation. Expect a good hit rate, not determinism.
- **`difft` and `ripgrep` are optional.** Without `difft` the engine falls back
  to its structural text engine and stamps `engine: "text"` on the affected
  entries. Without `ripgrep`, symbol lookup falls back to `git grep`.
- **The review never writes.** The engine is read-only by construction, and the
  skill instructs the reviewer not to edit the repository.
